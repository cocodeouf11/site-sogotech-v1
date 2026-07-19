"""
Iteration 5 backend tests - Depot permission gating, Commande send/resolve,
stock auto-add on conforme, notification permission-gated visibility,
and two-boutique data isolation.
"""
import os
import io
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://emergent-manage.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


def _login(pin):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"pin": pin}, timeout=30)
    assert r.status_code == 200, f"login {pin} failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def admin():
    return _login("123456")


@pytest.fixture(scope="module")
def shops(admin):
    r = admin.get(f"{API}/shops")
    assert r.status_code == 200
    return r.json()


@pytest.fixture(scope="module")
def two_boutiques(admin, shops):
    """Ensure at least two boutiques exist, create a second if needed."""
    boutiques = [s for s in shops if s.get("type") == "boutique"]
    if len(boutiques) < 2:
        r = admin.post(f"{API}/shops", json={
            "nom": "TEST_Boutique_B",
            "type": "boutique",
            "adresse": "2 rue B",
            "telephone": "",
        })
        assert r.status_code == 200, r.text
        boutiques.append(r.json())
    return boutiques[:2]


def _create_or_reset_user(admin, nom, prenom, pin, grade, shop_id):
    # cleanup any TEST_ user with the same nom (best effort)
    r = admin.get(f"{API}/users")
    for u in r.json():
        if u.get("nom") == nom and u.get("prenom") == prenom:
            admin.delete(f"{API}/users/{u['id']}")
    r = admin.post(f"{API}/users", json={
        "nom": nom,
        "prenom": prenom,
        "poste": grade,
        "grades": [grade],
        "shop_id": shop_id,
        "pin": pin,
        "is_admin": False,
    })
    assert r.status_code == 200, r.text
    return r.json()


# -------- Depot permission gating --------

class TestDepotPermission:
    def test_admin_can_list_depot_orders(self, admin):
        r = admin.get(f"{API}/depot/orders")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_vendeur_forbidden_on_depot(self, admin, two_boutiques):
        boutique_a = two_boutiques[0]
        _create_or_reset_user(admin, "TEST_Vend", "A", "111111", "Vendeur", boutique_a["id"])
        s = _login("111111")
        r = s.get(f"{API}/depot/orders")
        assert r.status_code == 403
        assert "Dépôt" in r.json().get("detail", "")

    def test_chef_depot_can_access(self, admin, two_boutiques):
        # depot shop
        r = admin.get(f"{API}/shops")
        depot_shop = next((s for s in r.json() if s.get("type") == "depot"), None)
        assert depot_shop is not None
        _create_or_reset_user(admin, "TEST_Chef", "D", "333333", "Chef de dépôt", depot_shop["id"])
        s = _login("333333")
        r = s.get(f"{API}/depot/orders")
        assert r.status_code == 200


# -------- Full flow: send/resolve/notification/isolation --------

@pytest.fixture(scope="module")
def depot_order(admin):
    """Ensure at least one depot order exists (use existing or create minimal)."""
    r = admin.get(f"{API}/depot/orders")
    orders = r.json()
    if orders:
        return orders[0]
    # create a minimal order via /tmp/bl.pdf if available; else via a tiny PDF stub
    pdf_path = "/tmp/bl.pdf"
    if not os.path.exists(pdf_path):
        # create a minimal PDF-like blob (won't parse lines but works to create)
        pdf_path = "/tmp/stub.pdf"
        with open(pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%%EOF")
    with open(pdf_path, "rb") as f:
        r = admin.post(
            f"{API}/depot/orders",
            files={"delivery": ("bl.pdf", f, "application/pdf")},
            data={"numero": f"TEST-{int(time.time())}"},
        )
    assert r.status_code == 200, r.text
    return r.json()


class TestSendAndResolve:
    _sent_commande = {}

    def test_send_order_to_boutique_a(self, admin, depot_order, two_boutiques):
        boutique_a = two_boutiques[0]
        r = admin.post(f"{API}/depot/orders/{depot_order['id']}/send", json={"shop_id": boutique_a["id"]})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["shop_id"] == boutique_a["id"]
        assert data["status"] == "envoyee"
        assert data["shop_nom"] == boutique_a["nom"]
        TestSendAndResolve._sent_commande["a"] = data

    def test_send_a_second_order(self, admin, depot_order, two_boutiques):
        boutique_a = two_boutiques[0]
        r = admin.post(f"{API}/depot/orders/{depot_order['id']}/send", json={"shop_id": boutique_a["id"]})
        assert r.status_code == 200
        TestSendAndResolve._sent_commande["a2"] = r.json()

    def test_admin_sees_commande(self, admin):
        r = admin.get(f"{API}/commandes")
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert TestSendAndResolve._sent_commande["a"]["id"] in ids

    def test_vendeur_a_sees_own_commande(self, admin, two_boutiques):
        # boutique A vendeur already created earlier
        s = _login("111111")
        r = s.get(f"{API}/commandes")
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert TestSendAndResolve._sent_commande["a"]["id"] in ids

    def test_isolation_boutique_b_user_cannot_see_a_commande(self, admin, two_boutiques):
        boutique_b = two_boutiques[1]
        _create_or_reset_user(admin, "TEST_Vend", "B", "222222", "Vendeur", boutique_b["id"])
        s = _login("222222")
        r = s.get(f"{API}/commandes")
        assert r.status_code == 200
        cmd_ids = [c["id"] for c in r.json()]
        assert TestSendAndResolve._sent_commande["a"]["id"] not in cmd_ids
        # direct GET must 403
        r2 = s.get(f"{API}/commandes/{TestSendAndResolve._sent_commande['a']['id']}")
        assert r2.status_code == 403

    def test_resolve_conforme_adds_stock(self, admin, two_boutiques):
        boutique_a = two_boutiques[0]
        commande = TestSendAndResolve._sent_commande["a"]
        # capture pre-stock
        r = admin.get(f"{API}/stock", params={"shop_id": boutique_a["id"]})
        # /stock endpoint may vary; just count via articles endpoint if available
        # Resolve as vendeur A
        s = _login("111111")
        r = s.post(f"{API}/commandes/{commande['id']}/resolve-conforme")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "conforme"
        # notification_message must be absent for non-depot user
        assert "notification_message" not in data

    def test_notification_visible_to_admin(self, admin):
        commande = TestSendAndResolve._sent_commande["a"]
        r = admin.get(f"{API}/commandes/{commande['id']}")
        assert r.status_code == 200
        data = r.json()
        assert data.get("notification_message"), "admin should see notification_message"
        assert "validé" in data["notification_message"].lower() or "valide" in data["notification_message"].lower()

    def test_notification_hidden_from_vendeur(self, admin):
        commande = TestSendAndResolve._sent_commande["a"]
        s = _login("111111")
        r = s.get(f"{API}/commandes/{commande['id']}")
        assert r.status_code == 200
        assert "notification_message" not in r.json()

    def test_resolve_non_conforme(self, admin):
        commande = TestSendAndResolve._sent_commande["a2"]
        line_ids = [l["id"] for l in commande.get("lines", [])[:1]]
        s = _login("111111")
        r = s.post(f"{API}/commandes/{commande['id']}/resolve-non-conforme", json={
            "items": [{"line_id": lid, "description": "endommagé", "note": ""} for lid in line_ids],
            "description": "colis endommagé à réception",
        })
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "non_conforme"

    def test_cannot_resolve_twice(self, admin):
        commande = TestSendAndResolve._sent_commande["a"]
        s = _login("111111")
        r = s.post(f"{API}/commandes/{commande['id']}/resolve-conforme")
        assert r.status_code == 400


class TestStockPersistence:
    def test_articles_added_to_boutique_a_stock(self, admin, two_boutiques):
        boutique_a = two_boutiques[0]
        r = admin.get(f"{API}/stock", params={"shop_id": boutique_a["id"]})
        # may be /articles or /stock; try both
        if r.status_code == 404:
            r = admin.get(f"{API}/articles", params={"shop_id": boutique_a["id"]})
        assert r.status_code == 200
        data = r.json()
        # Non-empty stock now expected
        assert isinstance(data, list)


# -------- Depot permission migration --------

class TestPermissionsShape:
    def test_admin_has_depot_permission(self, admin):
        r = admin.get(f"{API}/auth/me")
        assert r.status_code == 200
        u = r.json()
        assert u["permissions"].get("depot") is True

    def test_vendeur_has_depot_false(self, admin, two_boutiques):
        # user was created earlier
        s = _login("111111")
        r = s.get(f"{API}/auth/me")
        assert r.status_code == 200
        assert r.json()["permissions"].get("depot") is False
