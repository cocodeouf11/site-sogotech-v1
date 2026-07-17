"""
Tests for new/modified Dépôt features:
- create_order now takes optional Form 'numero' (auto-extract from PDF)
- parse_delivery_lines() extracts UGS/Étagère/Colonne/Tiroir/Bac metadata
- extract_order_number() reads 'N° de commande :' + next line
- POST /orders/{id}/lines/{line_id}/tap cycles quantite_picked
"""
import io
import os
import pytest
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"
ADMIN_PIN = "123456"


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"pin": ADMIN_PIN})
    assert r.status_code == 200
    return s


def _build_bl_pdf(numero: str, products):
    """Builds a bon-de-livraison PDF resembling the real French BL layout."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(50, 800, "BON DE LIVRAISON")
    c.drawString(50, 780, "N° de commande :")
    c.drawString(50, 765, numero)
    c.drawString(50, 730, "Produits")
    c.drawString(400, 730, "Quantité")
    y = 700
    for p in products:
        c.drawString(50, y, p["desc"])
        y -= 15
        meta = f"UGS : {p['ugs']}  Étagère : {p['etagere']} | Colonne : {p['colonne']} | Tiroir : {p['tiroir']} | Bac : {p['bac']}"
        c.drawString(50, y, meta)
        y -= 15
        c.drawString(50, y, str(p["qty"]))
        y -= 20
    c.showPage()
    c.save()
    return buf.getvalue()


PRODUCTS = [
    {"desc": "Coque iPhone 12 Pro", "ugs": "COQ001", "etagere": "A", "colonne": "1", "tiroir": "2", "bac": "L", "qty": 3},
    {"desc": "Verre trempé iPhone 13", "ugs": "VT013", "etagere": "B", "colonne": "2", "tiroir": "1", "bac": "M", "qty": 1},
    {"desc": "Chargeur USB-C 20W", "ugs": "CHG20", "etagere": "C", "colonne": "3", "tiroir": "4", "bac": "S", "qty": 5},
]


def test_create_order_without_numero_auto_extract(admin_session):
    """POST /depot/orders with no numero form field -> auto extract from PDF."""
    pdf = _build_bl_pdf("TEST_AUTO-99999", PRODUCTS)
    files = {"delivery": ("bl.pdf", pdf, "application/pdf")}
    r = admin_session.post(f"{API}/depot/orders", files=files)
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["numero"] == "TEST_AUTO-99999", f"Expected auto-extract, got {order['numero']}"
    assert isinstance(order["lines"], list)
    assert len(order["lines"]) >= 1, f"Expected parsed lines, got {order['lines']}"
    # Verify metadata parsed
    line0 = order["lines"][0]
    assert "ugs" in line0
    assert "etagere" in line0
    assert "colonne" in line0
    assert "tiroir" in line0
    assert "bac" in line0
    admin_session.delete(f"{API}/depot/orders/{order['id']}")


def test_parse_lines_metadata_fields(admin_session):
    pdf = _build_bl_pdf("TEST_META-1", PRODUCTS)
    files = {"delivery": ("bl.pdf", pdf, "application/pdf")}
    r = admin_session.post(f"{API}/depot/orders", files=files)
    assert r.status_code == 200
    order = r.json()
    # We should have 3 lines
    assert len(order["lines"]) == 3, f"Expected 3 lines, got {len(order['lines'])}: {order['lines']}"
    # Check first line matches expected metadata
    first = order["lines"][0]
    assert first["ugs"] == "COQ001", f"UGS mismatch: {first}"
    assert first["etagere"] == "A"
    assert first["colonne"] == "1"
    assert first["tiroir"] == "2"
    assert first["bac"] == "L"
    assert first["quantite_attendue"] == 3
    assert first["quantite_picked"] == 0
    # Total qty
    total = sum(l["quantite_attendue"] for l in order["lines"])
    assert total == 9  # 3+1+5
    admin_session.delete(f"{API}/depot/orders/{order['id']}")


def test_tap_endpoint_increments_and_cycles(admin_session):
    """POST tap endpoint: increments quantite_picked by 1, cycles to 0 at max."""
    pdf = _build_bl_pdf("TEST_TAP-1", [PRODUCTS[0]])  # qty=3
    files = {"delivery": ("bl.pdf", pdf, "application/pdf")}
    r = admin_session.post(f"{API}/depot/orders", files=files)
    assert r.status_code == 200
    order = r.json()
    assert len(order["lines"]) == 1
    oid = order["id"]
    lid = order["lines"][0]["id"]
    # Initially en_attente
    assert order["status"] == "en_attente"
    # tap #1 -> 1
    r1 = admin_session.post(f"{API}/depot/orders/{oid}/lines/{lid}/tap")
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["lines"][0]["quantite_picked"] == 1
    assert d1["status"] == "en_cours"
    # tap #2 -> 2
    r2 = admin_session.post(f"{API}/depot/orders/{oid}/lines/{lid}/tap")
    assert r2.json()["lines"][0]["quantite_picked"] == 2
    # tap #3 -> 3 (fully picked, status termine)
    r3 = admin_session.post(f"{API}/depot/orders/{oid}/lines/{lid}/tap")
    d3 = r3.json()
    assert d3["lines"][0]["quantite_picked"] == 3
    assert d3["status"] == "termine"
    # tap #4 -> cycles back to 0
    r4 = admin_session.post(f"{API}/depot/orders/{oid}/lines/{lid}/tap")
    d4 = r4.json()
    assert d4["lines"][0]["quantite_picked"] == 0, f"Expected reset to 0 at max, got {d4['lines'][0]['quantite_picked']}"
    assert d4["status"] == "en_attente"
    admin_session.delete(f"{API}/depot/orders/{oid}")


def test_tap_single_qty_marks_done(admin_session):
    """Line with quantity=1: one tap => done (status termine when only line)."""
    pdf = _build_bl_pdf("TEST_TAP1-1", [PRODUCTS[1]])  # qty=1
    files = {"delivery": ("bl.pdf", pdf, "application/pdf")}
    r = admin_session.post(f"{API}/depot/orders", files=files)
    order = r.json()
    oid = order["id"]
    lid = order["lines"][0]["id"]
    r1 = admin_session.post(f"{API}/depot/orders/{oid}/lines/{lid}/tap")
    d = r1.json()
    assert d["lines"][0]["quantite_picked"] == 1
    assert d["lines"][0]["quantite_attendue"] == 1
    assert d["status"] == "termine"
    admin_session.delete(f"{API}/depot/orders/{oid}")


def test_status_transitions(admin_session):
    """en_attente -> en_cours -> termine across multiple lines."""
    pdf = _build_bl_pdf("TEST_STATUS-1", PRODUCTS)
    files = {"delivery": ("bl.pdf", pdf, "application/pdf")}
    r = admin_session.post(f"{API}/depot/orders", files=files)
    order = r.json()
    oid = order["id"]
    lines = order["lines"]
    assert order["status"] == "en_attente"

    # Tap first line once -> en_cours
    r1 = admin_session.post(f"{API}/depot/orders/{oid}/lines/{lines[0]['id']}/tap")
    assert r1.json()["status"] == "en_cours"

    # Fill all lines to complete
    for line in lines:
        remaining = line["quantite_attendue"] - (1 if line["id"] == lines[0]["id"] else 0)
        for _ in range(remaining):
            admin_session.post(f"{API}/depot/orders/{oid}/lines/{line['id']}/tap")
    # get final state
    rf = admin_session.get(f"{API}/depot/orders/{oid}")
    assert rf.json()["status"] == "termine"
    admin_session.delete(f"{API}/depot/orders/{oid}")


def test_create_order_with_form_numero_override(admin_session):
    """If numero is provided as Form data, it overrides auto-extract."""
    pdf = _build_bl_pdf("PDF-EXTRACT-1", [PRODUCTS[0]])
    files = {"delivery": ("bl.pdf", pdf, "application/pdf")}
    data = {"numero": "TEST_MANUAL-777"}
    r = admin_session.post(f"{API}/depot/orders", files=files, data=data)
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["numero"] == "TEST_MANUAL-777", f"Expected manual numero, got {order['numero']}"
    admin_session.delete(f"{API}/depot/orders/{order['id']}")


def test_create_order_no_numero_no_extract_fallback(admin_session):
    """PDF without 'N° de commande' => fallback to CMD-<timestamp>."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.drawString(50, 800, "Just a plain PDF")
    c.showPage()
    c.save()
    files = {"delivery": ("bl.pdf", buf.getvalue(), "application/pdf")}
    r = admin_session.post(f"{API}/depot/orders", files=files)
    assert r.status_code == 200
    order = r.json()
    assert order["numero"].startswith("CMD-"), f"Expected CMD-timestamp fallback, got {order['numero']}"
    admin_session.delete(f"{API}/depot/orders/{order['id']}")
