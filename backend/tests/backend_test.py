"""
Comprehensive backend test suite for Boutique/Dépôt app.
Covers: auth (PIN), users/permissions, shops, stock, caisse, intervention,
devis, reprise, communication, depot picking orders, data isolation, PDFs.
"""
import io
import os
import time
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else "https://emergent-manage.preview.emergentagent.com"
API = f"{BASE}/api"
ADMIN_PIN = "123456"


# ------------------------- helpers / fixtures -------------------------

def _client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _login(session, pin):
    r = session.post(f"{API}/auth/login", json={"pin": pin})
    return r


@pytest.fixture(scope="session")
def admin_session():
    s = _client()
    r = _login(s, ADMIN_PIN)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def admin_user(admin_session):
    r = admin_session.get(f"{API}/auth/me")
    assert r.status_code == 200
    return r.json()


@pytest.fixture(scope="session")
def shops(admin_session):
    r = admin_session.get(f"{API}/shops")
    assert r.status_code == 200
    return r.json()


@pytest.fixture(scope="session")
def boutique_shop_id(shops):
    for s in shops:
        if s.get("type") == "boutique":
            return s["id"]
    pytest.skip("No boutique shop seeded")


# ------------------------- auth -------------------------

class TestAuth:
    def test_login_admin_ok(self):
        s = _client()
        r = _login(s, ADMIN_PIN)
        assert r.status_code == 200
        data = r.json()
        assert "user" in data
        assert data["user"].get("is_admin") is True
        # cookie set
        assert "access_token" in s.cookies or data.get("token")

    def test_login_wrong_pin(self):
        s = _client()
        r = _login(s, "000000")
        assert r.status_code == 401

    def test_me_returns_user(self, admin_session):
        r = admin_session.get(f"{API}/auth/me")
        assert r.status_code == 200
        u = r.json()
        assert u.get("is_admin") is True
        assert "pin_hash" not in u

    def test_me_unauthenticated(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401


# ------------------------- shops -------------------------

class TestShops:
    def test_list_shops(self, admin_session):
        r = admin_session.get(f"{API}/shops")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        types = [s.get("type") for s in data]
        assert "boutique" in types
        assert "depot" in types

    def test_create_and_update_shop(self, admin_session):
        r = admin_session.post(f"{API}/shops", json={
            "nom": "TEST_Shop", "type": "boutique",
            "adresse": "1 rue test", "telephone": "0100000000",
        })
        assert r.status_code == 200, r.text
        shop = r.json()
        assert shop["nom"] == "TEST_Shop"
        sid = shop["id"]
        r2 = admin_session.patch(f"{API}/shops/{sid}", json={"telephone": "0111111111"})
        assert r2.status_code == 200
        assert r2.json()["telephone"] == "0111111111"
        # delete
        r3 = admin_session.delete(f"{API}/shops/{sid}")
        assert r3.status_code == 200


# ------------------------- users / permissions -------------------------

@pytest.fixture(scope="session")
def vendeur_user(admin_session, boutique_shop_id):
    # create a Vendeur (limited perms) for isolation tests
    pin = "654321"
    r = admin_session.post(f"{API}/users", json={
        "nom": "TEST_Vendeur",
        "prenom": "Jean",
        "poste": "Vendeur",
        "grades": ["Vendeur"],
        "shop_id": boutique_shop_id,
        "telephone": "",
        "pin": pin,
    })
    assert r.status_code == 200, r.text
    user = r.json()
    yield {"id": user["id"], "pin": pin, "shop_id": boutique_shop_id}
    admin_session.delete(f"{API}/users/{user['id']}")


@pytest.fixture(scope="session")
def vendeur_session(vendeur_user):
    s = _client()
    r = _login(s, vendeur_user["pin"])
    assert r.status_code == 200
    return s


class TestUsers:
    def test_list_users(self, admin_session):
        r = admin_session.get(f"{API}/users")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_grades_endpoint(self, admin_session):
        r = admin_session.get(f"{API}/users/grades")
        assert r.status_code == 200
        grades = r.json().get("grades", [])
        assert "Vendeur" in grades
        assert "Magasinier" in grades

    def test_create_user_invalid_pin(self, admin_session, boutique_shop_id):
        r = admin_session.post(f"{API}/users", json={
            "nom": "X", "prenom": "Y", "poste": "Vendeur", "grades": ["Vendeur"],
            "shop_id": boutique_shop_id, "pin": "12"
        })
        assert r.status_code == 400

    def test_non_admin_cannot_create_user(self, vendeur_session, boutique_shop_id):
        r = vendeur_session.post(f"{API}/users", json={
            "nom": "Z", "prenom": "Z", "poste": "Vendeur", "grades": ["Vendeur"],
            "shop_id": boutique_shop_id, "pin": "111222"
        })
        assert r.status_code == 403

    def test_admin_edit_permissions(self, admin_session, vendeur_user):
        # Grant delete stock permission via override
        r = admin_session.patch(f"{API}/users/{vendeur_user['id']}", json={
            "permissions": {"stock": {"delete": True}}
        })
        assert r.status_code == 200
        user = r.json()
        assert user["permissions"]["stock"]["delete"] is True
        # revert
        admin_session.patch(f"{API}/users/{vendeur_user['id']}", json={
            "permissions": {"stock": {"delete": False}}
        })


# ------------------------- stock -------------------------

@pytest.fixture(scope="session")
def stock_article(admin_session, boutique_shop_id):
    r = admin_session.post(f"{API}/stock", json={
        "nom": "TEST_Article", "quantite": 10, "categorie": "coques",
        "shop_id": boutique_shop_id, "prix": 12.5,
    })
    assert r.status_code == 200, r.text
    a = r.json()
    yield a
    admin_session.delete(f"{API}/stock/{a['id']}")


class TestStock:
    def test_create_and_get_article(self, admin_session, stock_article):
        r = admin_session.get(f"{API}/stock")
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()]
        assert stock_article["id"] in ids

    def test_edit_quantity(self, admin_session, stock_article):
        r = admin_session.patch(f"{API}/stock/{stock_article['id']}", json={"quantite": 20})
        assert r.status_code == 200
        assert r.json()["quantite"] == 20

    def test_vendeur_cannot_add(self, vendeur_session, boutique_shop_id):
        r = vendeur_session.post(f"{API}/stock", json={
            "nom": "TEST_Denied", "quantite": 1, "shop_id": boutique_shop_id, "prix": 1.0,
        })
        assert r.status_code == 403

    def test_vendeur_cannot_delete(self, vendeur_session, stock_article):
        r = vendeur_session.delete(f"{API}/stock/{stock_article['id']}")
        assert r.status_code == 403

    def test_vendeur_can_view_list(self, vendeur_session):
        r = vendeur_session.get(f"{API}/stock")
        assert r.status_code == 200


# ------------------------- caisse -------------------------

class TestCaisse:
    def test_create_ticket_and_totals(self, admin_session, boutique_shop_id, stock_article):
        payload = {
            "type": "ticket",
            "shop_id": boutique_shop_id,
            "items": [
                {"type": "article", "article_id": stock_article["id"], "nom": stock_article["nom"], "prix_unitaire": 10.0, "quantite": 2},
                {"type": "prestation", "nom": "Nettoyage", "prix_unitaire": 5.0, "quantite": 1},
            ],
            "tva_percent": 20,
        }
        r = admin_session.post(f"{API}/caisse", json=payload)
        assert r.status_code == 200, r.text
        t = r.json()
        assert t["numero"].startswith("TIK-")
        assert t["total_ht"] == 25.0
        assert t["total_tva"] == 5.0
        assert t["total_ttc"] == 30.0
        # PDF
        r_pdf = admin_session.get(f"{API}/caisse/{t['id']}/pdf")
        assert r_pdf.status_code == 200
        assert "application/pdf" in r_pdf.headers.get("content-type", "")
        assert r_pdf.content[:4] == b"%PDF"

    def test_create_facture(self, admin_session, boutique_shop_id):
        payload = {
            "type": "facture", "shop_id": boutique_shop_id,
            "items": [{"type": "prestation", "nom": "Réparation", "prix_unitaire": 100.0, "quantite": 1}],
            "tva_percent": 20,
            "client_info": {"nom": "Dupont", "email": "d@d.fr"},
        }
        r = admin_session.post(f"{API}/caisse", json=payload)
        assert r.status_code == 200
        t = r.json()
        assert t["numero"].startswith("FAC-")
        assert t["total_ttc"] == 120.0

    def test_vendeur_cannot_delete_ticket(self, vendeur_session, admin_session, boutique_shop_id):
        r = admin_session.post(f"{API}/caisse", json={
            "type": "ticket", "shop_id": boutique_shop_id,
            "items": [{"type": "prestation", "nom": "X", "prix_unitaire": 1, "quantite": 1}],
        })
        assert r.status_code == 200
        tid = r.json()["id"]
        rd = vendeur_session.delete(f"{API}/caisse/{tid}")
        assert rd.status_code == 403
        admin_session.delete(f"{API}/caisse/{tid}")


# ------------------------- intervention / devis / reprise (+ PDF + isolation) -------------------------

@pytest.fixture(scope="session")
def second_shop(admin_session):
    r = admin_session.post(f"{API}/shops", json={"nom": "TEST_Shop2", "type": "boutique"})
    assert r.status_code == 200
    shop = r.json()
    yield shop
    admin_session.delete(f"{API}/shops/{shop['id']}")


class TestIntervention:
    def test_create_and_pdf(self, admin_session, boutique_shop_id):
        r = admin_session.post(f"{API}/interventions", json={
            "shop_id": boutique_shop_id,
            "client_nom": "TEST_Client",
            "client_tel": "0100000000",
            "materiel": "iPhone 12",
            "imei": "123456789012345",
            "motif": "Écran cassé",
            "intervention_effectuee": "Remplacement écran",
            "signature_data": "data:image/png;base64,iVBORw0KGgo=",
        })
        assert r.status_code == 200, r.text
        i = r.json()
        assert i["numero"].startswith("INT-")
        assert len(i["numero"].split("-")[-1]) == 4
        rp = admin_session.get(f"{API}/interventions/{i['id']}/pdf")
        assert rp.status_code == 200
        assert rp.content[:4] == b"%PDF"
        return i

    def test_list_with_can_open_flag(self, admin_session):
        r = admin_session.get(f"{API}/interventions")
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        if items:
            assert "can_open" in items[0]

    def test_vendeur_isolation(self, admin_session, vendeur_session, second_shop):
        # NOTE: admin can't just pass shop_id=second_shop in the payload anymore -- the
        # backend always overrides shop_id with the creator's own effective_shop_id
        # (security fix). So we create a throwaway user actually assigned to second_shop
        # to produce a genuine cross-shop document.
        r_u = admin_session.post(f"{API}/users", json={
            "nom": "TEST_SecondShopUser", "prenom": "X", "poste": "Vendeur",
            "grades": ["Vendeur"], "shop_id": second_shop["id"], "pin": "319001",
        })
        assert r_u.status_code == 200, r_u.text
        second_shop_user_id = r_u.json()["id"]
        s2 = _client()
        r_login = _login(s2, "319001")
        assert r_login.status_code == 200
        r = s2.post(f"{API}/interventions", json={
            "shop_id": second_shop["id"],
            "client_nom": "TEST_Isolated",
            "materiel": "S22",
        })
        assert r.status_code == 200
        other_id = r.json()["id"]
        # STRICT isolation (iteration 6): vendeur must NOT see other shop's intervention
        # at all in the list (not even locked/can_open=False).
        rl = vendeur_session.get(f"{API}/interventions")
        assert rl.status_code == 200
        found = [x for x in rl.json() if x["id"] == other_id]
        assert not found, "vendeur should NOT see other shop's intervention in list at all (strict cloisonnement)"
        # detail should still 403
        rd = vendeur_session.get(f"{API}/interventions/{other_id}")
        assert rd.status_code == 403
        admin_session.delete(f"{API}/interventions/{other_id}")
        admin_session.delete(f"{API}/users/{second_shop_user_id}")


class TestDevis:
    def test_create_devis_and_pdf(self, admin_session, boutique_shop_id):
        r = admin_session.post(f"{API}/devis", json={
            "shop_id": boutique_shop_id,
            "client_nom": "TEST_ClientDevis",
            "items": [
                {"nom": "Écran", "prix_unitaire": 80.0, "quantite": 1},
                {"nom": "Main d'œuvre", "prix_unitaire": 30.0, "quantite": 1},
            ],
            "intervention_ids": [],
            "mentions_legales": "Devis valable 30 jours",
            "signature_data": "data:image/png;base64,iVBORw0KGgo=",
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["numero"].startswith("DEV-")
        rp = admin_session.get(f"{API}/devis/{d['id']}/pdf")
        assert rp.status_code == 200
        assert rp.content[:4] == b"%PDF"


class TestReprise:
    def test_create_reprise_and_pdf(self, admin_session, boutique_shop_id):
        r = admin_session.post(f"{API}/reprises", json={
            "shop_id": boutique_shop_id,
            "client_nom": "TEST_ClientRep",
            "modele": "iPhone 11",
            "capacite": "64",
            "imei": "351234567890123",
            "etat_produit": {"fonctionnel": True, "deconnexion": True, "debloque": True},
            "tests": {"reseau": True, "camera": True},
            "batterie_pourcentage": 89,
            "remarques": "Rayures légères",
            "defauts_marks": [{"face": "avant", "x": 30, "y": 40}, {"face": "arriere", "x": 55, "y": 25}],
            "offre_rachat": 150.0,
            "bon_pour_accord": True,
            "signature_data": "data:image/png;base64,iVBORw0KGgo=",
        })
        assert r.status_code == 200, r.text
        rep = r.json()
        assert rep["numero"].startswith("REP-")
        assert rep["bon_pour_accord"] is True
        assert len(rep["defauts_marks"]) == 2
        rp = admin_session.get(f"{API}/reprises/{rep['id']}/pdf")
        assert rp.status_code == 200
        assert rp.content[:4] == b"%PDF"


# ------------------------- communication -------------------------

class TestCommunication:
    def test_send_and_list_message(self, admin_session, vendeur_user, admin_user):
        r = admin_session.post(f"{API}/communication/messages", json={
            "to_user_id": vendeur_user["id"],
            "content": "TEST_Hello",
        })
        assert r.status_code == 200
        m = r.json()
        assert m["content"] == "TEST_Hello"
        rl = admin_session.get(f"{API}/communication/messages", params={"with_user": vendeur_user["id"]})
        assert rl.status_code == 200
        assert any(x["content"] == "TEST_Hello" for x in rl.json())

    def test_help_ticket_flow(self, admin_session):
        r = admin_session.post(f"{API}/communication/tickets", json={
            "subject": "TEST_Bug", "description": "Serveur lent", "urgence": "elevee"
        })
        assert r.status_code == 200
        tid = r.json()["id"]
        # add comment
        rc = admin_session.post(f"{API}/communication/tickets/{tid}/comments", json={"content": "Ping"})
        assert rc.status_code == 200
        assert len(rc.json()["comments"]) == 1
        # change status
        ru = admin_session.patch(f"{API}/communication/tickets/{tid}", json={"status": "resolu"})
        assert ru.status_code == 200
        assert ru.json()["status"] == "resolu"


# ------------------------- depot -------------------------

def _make_pdf_bytes(lines):
    """Create a small PDF with product lines using reportlab."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    y = 800
    c.setFont("Helvetica", 12)
    c.drawString(50, y, "Bon de livraison test")
    y -= 30
    for l in lines:
        c.drawString(50, y, l)
        y -= 20
    c.showPage()
    c.save()
    return buf.getvalue()


class TestDepot:
    def test_create_order_with_pdf(self, admin_session):
        pdf = _make_pdf_bytes(["Coque iPhone 12  5", "Chargeur USB-C  10", "Verre trempe  3"])
        files = {"delivery": ("bl.pdf", pdf, "application/pdf")}
        # numero is now a Form field (not query param) after iteration 2 refactor
        s = requests.Session()
        s.cookies.update(admin_session.cookies)
        r = s.post(f"{API}/depot/orders", data={"numero": "TEST_BL-001"}, files=files)
        assert r.status_code == 200, r.text
        order = r.json()
        assert order["numero"] == "TEST_BL-001"
        assert isinstance(order["lines"], list)
        # Not asserting exact parse count (heuristic) but expect >=1 usually
        return order

    def test_add_manual_line_and_increment(self, admin_session):
        pdf = _make_pdf_bytes(["Empty"])
        files = {"delivery": ("bl.pdf", pdf, "application/pdf")}
        s = requests.Session()
        s.cookies.update(admin_session.cookies)
        r = s.post(f"{API}/depot/orders", data={"numero": "TEST_BL-002"}, files=files)
        assert r.status_code == 200
        order = r.json()
        oid = order["id"]
        # Add manual line
        r_add = admin_session.post(f"{API}/depot/orders/{oid}/lines", json={"description": "Prod X", "quantite_attendue": 3})
        assert r_add.status_code == 200
        order = r_add.json()
        line_id = order["lines"][-1]["id"]
        # increment +1 three times => full
        for _ in range(3):
            r_inc = admin_session.post(f"{API}/depot/orders/{oid}/lines/{line_id}/increment", json={"delta": 1})
            assert r_inc.status_code == 200
        final = r_inc.json()
        # All picked -> status termine (only this one line was added; parse may have added others)
        line = [l for l in final["lines"] if l["id"] == line_id][0]
        assert line["quantite_picked"] == 3
        # reset
        r_res = admin_session.post(f"{API}/depot/orders/{oid}/lines/{line_id}/increment", json={"reset": True})
        assert r_res.status_code == 200
        line = [l for l in r_res.json()["lines"] if l["id"] == line_id][0]
        assert line["quantite_picked"] == 0
        # cleanup
        admin_session.delete(f"{API}/depot/orders/{oid}")
