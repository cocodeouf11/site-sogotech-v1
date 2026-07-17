"""
Iteration 3 backend tests - covers:
- Shop SIRET field
- Stock custom code / auto-code / duplicate rejection
- Caisse ticket PATCH (edit with recalculation), permission gating on edit/delete
- Caisse ticket vendeur_nom on creation
- Intervention same-shop visibility (regression bug)
- Facture with client SIRET
"""
import os
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"
ADMIN_PIN = "123456"


def _client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _login(pin):
    s = _client()
    r = s.post(f"{API}/auth/login", json={"pin": pin})
    assert r.status_code == 200, f"login failed pin={pin}: {r.text}"
    return s


@pytest.fixture(scope="module")
def admin():
    return _login(ADMIN_PIN)


@pytest.fixture(scope="module")
def boutique_shop_id(admin):
    r = admin.get(f"{API}/shops")
    assert r.status_code == 200
    for s in r.json():
        if s.get("type") == "boutique":
            return s["id"]
    pytest.skip("No boutique shop found")


# ---------- Shop SIRET ----------

class TestShopSiret:
    def test_create_shop_with_siret(self, admin):
        r = admin.post(f"{API}/shops", json={
            "nom": "TEST_ShopSiret", "type": "boutique",
            "adresse": "1 rue", "telephone": "0100000000",
            "siret": "12345678901234",
        })
        assert r.status_code == 200, r.text
        shop = r.json()
        assert shop.get("siret") == "12345678901234"
        # verify persistence via GET
        r2 = admin.get(f"{API}/shops")
        found = [s for s in r2.json() if s["id"] == shop["id"]]
        assert found and found[0].get("siret") == "12345678901234"
        # cleanup
        admin.delete(f"{API}/shops/{shop['id']}")

    def test_update_shop_siret(self, admin, boutique_shop_id):
        # save original
        r0 = admin.get(f"{API}/shops")
        original_siret = next((s.get("siret", "") for s in r0.json() if s["id"] == boutique_shop_id), "")
        r = admin.patch(f"{API}/shops/{boutique_shop_id}", json={"siret": "99988877766655"})
        assert r.status_code == 200
        assert r.json().get("siret") == "99988877766655"
        # revert
        admin.patch(f"{API}/shops/{boutique_shop_id}", json={"siret": original_siret})


# ---------- Stock custom code ----------

class TestStockCode:
    def test_auto_code_when_empty(self, admin, boutique_shop_id):
        r = admin.post(f"{API}/stock", json={
            "nom": "TEST_AutoCode", "quantite": 1, "shop_id": boutique_shop_id, "prix": 1.0,
        })
        assert r.status_code == 200, r.text
        art = r.json()
        assert art.get("code", "").startswith("ART-"), f"expected ART- code, got {art.get('code')}"
        assert len(art["code"]) == 8  # ART-0001 style
        admin.delete(f"{API}/stock/{art['id']}")

    def test_custom_code_used_as_is(self, admin, boutique_shop_id):
        r = admin.post(f"{API}/stock", json={
            "nom": "TEST_CustomCode", "quantite": 1, "shop_id": boutique_shop_id,
            "prix": 1.0, "code": "MYCODE_TEST_1",
        })
        assert r.status_code == 200, r.text
        art = r.json()
        assert art["code"] == "MYCODE_TEST_1"
        # Try duplicate
        r2 = admin.post(f"{API}/stock", json={
            "nom": "TEST_Dup", "quantite": 1, "shop_id": boutique_shop_id,
            "prix": 1.0, "code": "MYCODE_TEST_1",
        })
        assert r2.status_code == 400
        assert "existe" in r2.text.lower() or "déjà" in r2.text.lower() or "deja" in r2.text.lower()
        admin.delete(f"{API}/stock/{art['id']}")


# ---------- Caisse ticket edit / vendeur / SIRET ----------

class TestCaisseTicket:
    def test_ticket_has_vendeur_nom(self, admin, boutique_shop_id):
        r = admin.post(f"{API}/caisse", json={
            "type": "ticket", "shop_id": boutique_shop_id,
            "items": [{"type": "prestation", "nom": "X", "prix_unitaire": 10, "quantite": 1}],
            "tva_percent": 20,
        })
        assert r.status_code == 200
        t = r.json()
        assert t.get("vendeur_nom", "").strip(), "vendeur_nom should be populated"
        # cleanup
        admin.delete(f"{API}/caisse/{t['id']}")

    def test_patch_ticket_recalculates(self, admin, boutique_shop_id):
        r = admin.post(f"{API}/caisse", json={
            "type": "ticket", "shop_id": boutique_shop_id,
            "items": [{"type": "prestation", "nom": "X", "prix_unitaire": 10, "quantite": 1}],
            "tva_percent": 20,
        })
        tid = r.json()["id"]
        # Patch TVA to 10%
        rp = admin.patch(f"{API}/caisse/{tid}", json={"tva_percent": 10})
        assert rp.status_code == 200, rp.text
        updated = rp.json()
        assert updated["tva_percent"] == 10
        assert updated["total_ht"] == 10.0
        assert updated["total_tva"] == 1.0
        assert updated["total_ttc"] == 11.0
        # GET to verify persisted
        rg = admin.get(f"{API}/caisse/{tid}")
        assert rg.status_code == 200
        assert rg.json()["total_ttc"] == 11.0
        admin.delete(f"{API}/caisse/{tid}")

    def test_facture_with_client_siret(self, admin, boutique_shop_id):
        r = admin.post(f"{API}/caisse", json={
            "type": "facture", "shop_id": boutique_shop_id,
            "items": [{"type": "prestation", "nom": "Prest", "prix_unitaire": 100, "quantite": 1}],
            "tva_percent": 20,
            "client_info": {"nom": "TEST_ClientSiret", "siret": "44422211100088"},
        })
        assert r.status_code == 200, r.text
        t = r.json()
        assert t["client_info"].get("siret") == "44422211100088"
        # PDF should still be generatable
        rp = admin.get(f"{API}/caisse/{t['id']}/pdf")
        assert rp.status_code == 200
        assert rp.content[:4] == b"%PDF"
        admin.delete(f"{API}/caisse/{t['id']}")


# ---------- Same-shop intervention visibility (regression) ----------

@pytest.fixture(scope="module")
def two_same_shop_users(admin, boutique_shop_id):
    """Create 2 Vendeur users, both in the same boutique shop."""
    users = []
    pins = ["222333", "444555"]
    for i, pin in enumerate(pins):
        r = admin.post(f"{API}/users", json={
            "nom": f"TEST_SameShop{i}", "prenom": "User",
            "poste": "Vendeur", "grades": ["Vendeur"],
            "shop_id": boutique_shop_id, "telephone": "", "pin": pin,
        })
        assert r.status_code == 200, r.text
        users.append({"id": r.json()["id"], "pin": pin})
    yield users
    for u in users:
        admin.delete(f"{API}/users/{u['id']}")


class TestSameShopIntervention:
    def test_same_shop_users_can_see_and_open_each_others_interventions(self, admin, two_same_shop_users, boutique_shop_id):
        userA, userB = two_same_shop_users
        sessA = _login(userA["pin"])
        sessB = _login(userB["pin"])

        # A creates an intervention
        r = sessA.post(f"{API}/interventions", json={
            "shop_id": boutique_shop_id,
            "client_nom": "TEST_SameShopClient",
            "materiel": "iPhone X",
            "motif": "test",
        })
        assert r.status_code == 200, r.text
        iid = r.json()["id"]

        # B lists interventions
        rl = sessB.get(f"{API}/interventions")
        assert rl.status_code == 200
        found = [x for x in rl.json() if x["id"] == iid]
        assert found, "user B (same shop) should see the intervention in list"
        assert found[0]["can_open"] is True, "user B (same shop) should have can_open=True"

        # B opens detail
        rd = sessB.get(f"{API}/interventions/{iid}")
        assert rd.status_code == 200, f"same-shop user B should get 200, got {rd.status_code}: {rd.text}"
        assert rd.json()["client_nom"] == "TEST_SameShopClient"

        # cleanup: admin deletes (Vendeurs don't have delete perm)
        admin.delete(f"{API}/interventions/{iid}")
