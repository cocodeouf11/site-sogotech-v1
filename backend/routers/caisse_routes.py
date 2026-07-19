from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import get_current_user, has_permission, effective_shop_id
from sharing_utils import ShareRequest, share_document, document_visibility_query, annotate_share, can_access_document
from pdf_utils import generate_facture_pdf, generate_ticket_pdf

router = APIRouter(prefix="/api/caisse", tags=["caisse"])


class TicketItem(BaseModel):
    type: str
    article_id: Optional[str] = None
    nom: str
    prix_unitaire: float
    quantite: float = 1


class TicketCreate(BaseModel):
    type: str
    shop_id: str
    items: List[TicketItem]
    tva_percent: float = 20
    client_info: Optional[dict] = None


class TicketUpdate(BaseModel):
    items: Optional[List[TicketItem]] = None
    tva_percent: Optional[float] = None
    client_info: Optional[dict] = None


def serialize(t: dict) -> dict:
    t = dict(t)
    t["id"] = str(t["_id"])
    t.pop("_id", None)
    return t


async def next_number(prefix: str) -> str:
    year = datetime.now(timezone.utc).year
    key = f"{prefix}-{year}"
    counter = await db.counters.find_one_and_update(
        {"_id": key}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    return f"{prefix}-{year}-{counter['seq']:04d}"


@router.get("")
async def list_tickets(user: dict = Depends(get_current_user)):
    tickets = await db.tickets.find(document_visibility_query(user)).sort("created_at", -1).to_list(2000)
    return [annotate_share(serialize(t), t, user) for t in tickets]


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_access_document(user, ticket):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    return annotate_share(serialize(ticket), ticket, user)


@router.post("")
async def create_ticket(payload: TicketCreate, user: dict = Depends(get_current_user)):
    eff = effective_shop_id(user)
    if not eff:
        raise HTTPException(status_code=400, detail="Veuillez sélectionner une boutique de travail")
    prefix = "FAC" if payload.type == "facture" else "TIK"
    numero = await next_number(prefix)
    items = [i.model_dump() for i in payload.items]
    ht_total = sum(i["prix_unitaire"] * i["quantite"] for i in items)
    tva_amount = ht_total * payload.tva_percent / 100
    doc = {
        "type": payload.type,
        "numero": numero,
        "shop_id": eff,
        "vendeur_id": user["_id"],
        "vendeur_nom": f"{user.get('prenom','')} {user.get('nom','')}",
        "date": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
        "items": items,
        "tva_percent": payload.tva_percent,
        "total_ht": ht_total,
        "total_tva": tva_amount,
        "total_ttc": ht_total + tva_amount,
        "client_info": payload.client_info or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.tickets.insert_one(doc)
    created = await db.tickets.find_one({"_id": result.inserted_id})
    for item in items:
        if item.get("type") == "article" and item.get("article_id"):
            await db.articles.update_one(
                {"_id": ObjectId(item["article_id"])}, {"$inc": {"quantite": -item["quantite"]}}
            )
    return serialize(created)


def can_manage_ticket(user: dict, ticket: dict) -> bool:
    access = can_access_document(user, ticket)
    if not access:
        return False
    if access["owner"]:
        return has_permission(user, "caisse", "delete_ticket") or ticket.get("vendeur_id") == user["_id"]
    return access["mode"] == "write"


@router.patch("/{ticket_id}")
async def update_ticket(ticket_id: str, payload: TicketUpdate, user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_manage_ticket(user, ticket):
        raise HTTPException(status_code=403, detail="Permission refusée")
    update_data = payload.model_dump(exclude_unset=True)
    if "items" in update_data:
        items = [dict(i) for i in update_data["items"]]
        update_data["items"] = items
    else:
        items = ticket["items"]
    tva_percent = update_data.get("tva_percent", ticket.get("tva_percent", 20))
    ht_total = sum(i["prix_unitaire"] * i["quantite"] for i in items)
    tva_amount = ht_total * tva_percent / 100
    update_data["total_ht"] = ht_total
    update_data["total_tva"] = tva_amount
    update_data["total_ttc"] = ht_total + tva_amount
    await db.tickets.update_one({"_id": ObjectId(ticket_id)}, {"$set": update_data})
    updated = await db.tickets.find_one({"_id": ObjectId(ticket_id)})
    return serialize(updated)


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: str, user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        raise HTTPException(status_code=404, detail="Introuvable")
    if ticket.get("shop_id") != effective_shop_id(user):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    if not has_permission(user, "caisse", "delete_ticket"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    await db.tickets.delete_one({"_id": ObjectId(ticket_id)})
    return {"success": True}


@router.post("/{ticket_id}/share")
async def share_ticket(ticket_id: str, payload: ShareRequest, user: dict = Depends(get_current_user)):
    return await share_document(db.tickets, ticket_id, payload, user, has_permission(user, "partage_document", "share"))


@router.get("/{ticket_id}/pdf")
async def ticket_pdf(ticket_id: str, user: dict = Depends(get_current_user)):
    ticket = await db.tickets.find_one({"_id": ObjectId(ticket_id)})
    if not ticket:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_access_document(user, ticket):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    shop = await db.shops.find_one({"_id": ObjectId(ticket["shop_id"])}) or {}
    if ticket["type"] == "facture":
        pdf_bytes = generate_facture_pdf(ticket, shop)
    else:
        pdf_bytes = generate_ticket_pdf(ticket, shop)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename={ticket['numero']}.pdf"
    })
