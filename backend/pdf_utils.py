import base64
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def _decode_signature(signature_data: str):
    if not signature_data or "," not in signature_data:
        return None
    try:
        header, b64 = signature_data.split(",", 1)
        return ImageReader(BytesIO(base64.b64decode(b64)))
    except Exception:
        return None


def _logo_reader(logo_url: str):
    if not logo_url:
        return None
    path = os.path.join(ROOT_DIR, logo_url.lstrip("/"))
    if os.path.exists(path):
        return ImageReader(path)
    return None


def draw_header(c: canvas.Canvas, shop: dict, page_width, y_top):
    logo = _logo_reader(shop.get("logo_url", ""))
    left = 20 * mm
    if logo:
        try:
            c.drawImage(logo, left, y_top - 20 * mm, width=20 * mm, height=20 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    text_x = left + 24 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(text_x, y_top - 6 * mm, shop.get("nom", "Boutique"))
    c.setFont("Helvetica", 9)
    c.drawString(text_x, y_top - 11 * mm, shop.get("adresse", ""))
    c.drawString(text_x, y_top - 16 * mm, f"Tél: {shop.get('telephone', '')}")
    c.setLineWidth(0.7)
    c.line(left, y_top - 23 * mm, page_width - 20 * mm, y_top - 23 * mm)
    return y_top - 30 * mm


def _wrap_text(c, text, x, y, max_width, font="Helvetica", size=9, leading=4.5 * mm):
    c.setFont(font, size)
    words = (text or "").split()
    line = ""
    for word in words:
        test = f"{line} {word}".strip()
        if c.stringWidth(test, font, size) > max_width:
            c.drawString(x, y, line)
            y -= leading
            line = word
        else:
            line = test
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def _field(c, label, value, x, y, width=None):
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, f"{label}:")
    c.setFont("Helvetica", 9)
    c.drawString(x + c.stringWidth(f"{label}: ", "Helvetica-Bold", 9), y, str(value or ""))


def generate_intervention_pdf(data: dict, shop: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 20 * mm, h - 15 * mm, f"N° {data.get('numero', '')}")
    y = draw_header(c, shop, w, h - 10 * mm)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, y, "FICHE D'INTERVENTION")
    y -= 10 * mm
    left = 20 * mm
    _field(c, "Vendeur", data.get("vendeur_nom"), left, y); y -= 6 * mm
    _field(c, "Date", data.get("date"), left, y); y -= 6 * mm
    _field(c, "Client", data.get("client_nom"), left, y); y -= 6 * mm
    _field(c, "Téléphone", data.get("client_tel"), left, y); y -= 6 * mm
    _field(c, "Email", data.get("client_email"), left, y); y -= 6 * mm
    _field(c, "Adresse", data.get("client_adresse"), left, y); y -= 6 * mm
    _field(c, "Matériel concerné", data.get("materiel"), left, y); y -= 6 * mm
    _field(c, "IMEI", data.get("imei"), left, y); y -= 10 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, y, "Motif de l'intervention")
    y -= 6 * mm
    c.rect(left, y - 30 * mm, w - 40 * mm, 30 * mm)
    _wrap_text(c, data.get("motif", ""), left + 3 * mm, y - 5 * mm, w - 46 * mm)
    y -= 36 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, y, "Intervention effectuée")
    y -= 6 * mm
    c.rect(left, y - 30 * mm, w - 40 * mm, 30 * mm)
    _wrap_text(c, data.get("intervention_effectuee", ""), left + 3 * mm, y - 5 * mm, w - 46 * mm)
    y -= 40 * mm

    sig = _decode_signature(data.get("signature_data"))
    c.setFont("Helvetica", 9)
    c.drawString(left, y, "Signature client:")
    c.rect(left, y - 25 * mm, 70 * mm, 25 * mm)
    if sig:
        try:
            c.drawImage(sig, left + 1 * mm, y - 24 * mm, width=68 * mm, height=23 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.save()
    buf.seek(0)
    return buf.read()


def generate_devis_pdf(data: dict, shop: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 20 * mm, h - 15 * mm, f"N° {data.get('numero', '')}")
    y = draw_header(c, shop, w, h - 10 * mm)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, y, "DEVIS")
    y -= 10 * mm
    left = 20 * mm
    _field(c, "Vendeur", data.get("vendeur_nom"), left, y); y -= 6 * mm
    _field(c, "Date", data.get("date"), left, y); y -= 6 * mm
    _field(c, "Client", data.get("client_nom"), left, y); y -= 6 * mm
    _field(c, "Téléphone", data.get("client_tel"), left, y); y -= 6 * mm
    y -= 4 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, y, "Désignation")
    c.drawString(w - 90 * mm, y, "Qté")
    c.drawString(w - 70 * mm, y, "Prix unit.")
    c.drawString(w - 40 * mm, y, "Total")
    y -= 5 * mm
    c.line(left, y, w - 20 * mm, y)
    y -= 5 * mm
    total = 0
    for item in data.get("items", []):
        line_total = float(item.get("prix_unitaire", 0)) * float(item.get("quantite", 1))
        total += line_total
        c.setFont("Helvetica", 9)
        c.drawString(left, y, str(item.get("nom", ""))[:55])
        c.drawString(w - 90 * mm, y, str(item.get("quantite", 1)))
        c.drawString(w - 70 * mm, y, f"{float(item.get('prix_unitaire', 0)):.2f} €")
        c.drawString(w - 40 * mm, y, f"{line_total:.2f} €")
        y -= 5.5 * mm
        if y < 60 * mm:
            c.showPage()
            y = h - 20 * mm
    y -= 3 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(w - 20 * mm, y, f"Total: {total:.2f} €")
    y -= 12 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "Mentions légales")
    y -= 5 * mm
    y = _wrap_text(c, data.get("mentions_legales", ""), left, y, w - 40 * mm, size=8)
    y -= 8 * mm

    sig = _decode_signature(data.get("signature_data"))
    c.setFont("Helvetica", 9)
    c.drawString(left, y, "Signature client (bon pour accord):")
    c.rect(left, y - 25 * mm, 70 * mm, 25 * mm)
    if sig:
        try:
            c.drawImage(sig, left + 1 * mm, y - 24 * mm, width=68 * mm, height=23 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.save()
    buf.seek(0)
    return buf.read()


REPRISE_DISCLAIMER = (
    "Le vendeur déclare être le propriétaire du produit repris et certifie l'avoir acquis de manière légale. "
    "Il autorise la boutique à revendre, réparer, recycler ou détruire le produit à sa discrétion. "
    "En cas de blocage ultérieur du produit (compte, mot de passe, opérateur), le vendeur s'engage à débloquer "
    "immédiatement le produit ou à rembourser intégralement la somme perçue lors de la reprise."
)


def generate_reprise_pdf(data: dict, shop: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 20 * mm, h - 15 * mm, f"N° {data.get('numero', '')}")
    y = draw_header(c, shop, w, h - 10 * mm)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, y, "FICHE DE REPRISE TÉLÉPHONE")
    y -= 10 * mm
    left = 20 * mm
    _field(c, "Vendeur", data.get("vendeur_nom"), left, y); y -= 6 * mm
    _field(c, "Date", data.get("date"), left, y); y -= 6 * mm
    _field(c, "Client", data.get("client_nom"), left, y); y -= 6 * mm
    _field(c, "Téléphone", data.get("client_tel"), left, y); y -= 6 * mm
    _field(c, "Modèle", data.get("modele"), left, y); y -= 6 * mm
    _field(c, "Capacité", data.get("capacite"), left, y); y -= 6 * mm
    _field(c, "IMEI", data.get("imei"), left, y); y -= 8 * mm

    etat = data.get("etat_produit", {})
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "État: " + ", ".join([k.replace("_", " ") for k, v in etat.items() if v]))
    y -= 8 * mm

    tests = data.get("tests", {})
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "Tests OK: " + ", ".join([k.replace("_", " ") for k, v in tests.items() if v]))
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, f"Pièce à remplacer: {data.get('piece_a_remplacer', '-')}    Offre de rachat: {data.get('offre_rachat', '-')} €")
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 9)
    c.drawString(left, y, "Remarques")
    y -= 5 * mm
    c.rect(left, y - 20 * mm, w - 40 * mm, 20 * mm)
    _wrap_text(c, data.get("remarques", ""), left + 3 * mm, y - 5 * mm, w - 46 * mm)
    y -= 28 * mm

    y = _wrap_text(c, REPRISE_DISCLAIMER, left, y, w - 40 * mm, size=8)
    y -= 8 * mm

    sig = _decode_signature(data.get("signature_data"))
    c.setFont("Helvetica", 9)
    accord = "☑" if data.get("bon_pour_accord") else "☐"
    c.drawString(left, y, f"{accord} Bon pour accord      Signature:")
    c.rect(left, y - 25 * mm, 70 * mm, 25 * mm)
    if sig:
        try:
            c.drawImage(sig, left + 1 * mm, y - 24 * mm, width=68 * mm, height=23 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.save()
    buf.seek(0)
    return buf.read()


def generate_facture_pdf(data: dict, shop: dict) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    is_facture = data.get("type") == "facture"
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 20 * mm, h - 15 * mm, f"N° {data.get('numero', '')}")
    y = draw_header(c, shop, w, h - 10 * mm)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, y, "FACTURE" if is_facture else "TICKET DE CAISSE")
    y -= 10 * mm
    left = 20 * mm
    _field(c, "Date", data.get("date"), left, y); y -= 6 * mm
    if is_facture:
        client = data.get("client_info", {}) or {}
        _field(c, "Client", client.get("nom"), left, y); y -= 6 * mm
        _field(c, "Adresse", client.get("adresse"), left, y); y -= 6 * mm
        _field(c, "Email", client.get("email"), left, y); y -= 6 * mm
    y -= 4 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(left, y, "Désignation")
    c.drawString(w - 90 * mm, y, "Qté")
    c.drawString(w - 70 * mm, y, "Prix unit.")
    c.drawString(w - 40 * mm, y, "Total")
    y -= 5 * mm
    c.line(left, y, w - 20 * mm, y)
    y -= 5 * mm
    ht_total = 0
    for item in data.get("items", []):
        line_total = float(item.get("prix_unitaire", 0)) * float(item.get("quantite", 1))
        ht_total += line_total
        c.setFont("Helvetica", 9)
        c.drawString(left, y, str(item.get("nom", ""))[:55])
        c.drawString(w - 90 * mm, y, str(item.get("quantite", 1)))
        c.drawString(w - 70 * mm, y, f"{float(item.get('prix_unitaire', 0)):.2f} €")
        c.drawString(w - 40 * mm, y, f"{line_total:.2f} €")
        y -= 5.5 * mm
        if y < 60 * mm:
            c.showPage()
            y = h - 20 * mm
    y -= 3 * mm
    c.line(left, y, w - 20 * mm, y)
    y -= 6 * mm
    tva_percent = float(data.get("tva_percent", 20))
    tva_amount = ht_total * tva_percent / 100
    c.setFont("Helvetica", 10)
    c.drawRightString(w - 20 * mm, y, f"Total HT: {ht_total:.2f} €"); y -= 5.5 * mm
    c.drawRightString(w - 20 * mm, y, f"TVA ({tva_percent:.0f}%): {tva_amount:.2f} €"); y -= 5.5 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(w - 20 * mm, y, f"Total TTC: {(ht_total + tva_amount):.2f} €")
    y -= 12 * mm

    if is_facture:
        c.setFont("Helvetica", 7)
        y = _wrap_text(
            c,
            "Mentions légales: TVA non récupérable sauf mention contraire. En cas de retard de paiement, des pénalités "
            "légales seront appliquées. Garantie légale de conformité applicable conformément au Code de la consommation.",
            left, y, w - 40 * mm, size=7,
        )
    c.save()
    buf.seek(0)
    return buf.read()


def generate_ticket_pdf(data: dict, shop: dict) -> bytes:
    width = 80 * mm
    height = 200 * mm
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    y = height - 8 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, y, shop.get("nom", "Boutique")); y -= 5 * mm
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, y, shop.get("adresse", "")); y -= 4 * mm
    c.drawCentredString(width / 2, y, f"Tél: {shop.get('telephone', '')}"); y -= 6 * mm
    c.line(3 * mm, y, width - 3 * mm, y); y -= 5 * mm
    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, f"Ticket N° {data.get('numero', '')}"); y -= 4 * mm
    c.drawString(3 * mm, y, f"Date: {data.get('date', '')}"); y -= 6 * mm
    ht_total = 0
    for item in data.get("items", []):
        line_total = float(item.get("prix_unitaire", 0)) * float(item.get("quantite", 1))
        ht_total += line_total
        c.setFont("Helvetica", 7)
        c.drawString(3 * mm, y, f"{item.get('quantite', 1)}x {str(item.get('nom',''))[:24]}")
        c.drawRightString(width - 3 * mm, y, f"{line_total:.2f}€")
        y -= 4 * mm
    c.line(3 * mm, y, width - 3 * mm, y); y -= 5 * mm
    tva_percent = float(data.get("tva_percent", 20))
    tva_amount = ht_total * tva_percent / 100
    c.setFont("Helvetica", 7)
    c.drawString(3 * mm, y, f"Total HT: {ht_total:.2f}€"); y -= 4 * mm
    c.drawString(3 * mm, y, f"TVA ({tva_percent:.0f}%): {tva_amount:.2f}€"); y -= 4 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(3 * mm, y, f"Total TTC: {(ht_total + tva_amount):.2f}€"); y -= 8 * mm
    c.setFont("Helvetica", 6)
    c.drawCentredString(width / 2, y, "Merci de votre visite !")
    c.save()
    buf.seek(0)
    return buf.read()
