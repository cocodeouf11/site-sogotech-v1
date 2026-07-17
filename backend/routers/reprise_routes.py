from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import get_current_user, has_permission, can_view_shop
from pdf_utils import generate_reprise_pdf

router = APIRouter(prefix="/api/reprises", tags=["reprises"])


class ReprisCreate(BaseModel):
    shop_id: str
    client_nom: str
    client_tel: Optional[str] = ""
    client_email: Optional[str] = ""
    client_adresse: Optional[str] = ""
    modele: Optional[str] = ""
    capacite: Optional[str] = ""
    imei: Optional[str] = ""
    etat_produit: dict = {}
    tests: dict = {}
    batterie_pourcentage: Optional[int] = None
    remarques: Optional[str] = ""
    defauts_marks: List[dict] = []
    piece_a_remplacer: Optional[str] = ""
    offre_rachat: Optional[float] = 0
    bon_pour_accord: bool = False
    signature_data: Optional[str] = ""


class ReprisUpdate(BaseModel):
    numero: Optional[str] = None
    client_nom: Optional[str] = None
    client_tel: Optional[str] = None
    client_email: Optional[str] = None
    client_adresse: Optional[str] = None
    modele: Optional[str] = None
    capacite: Optional[str] = None
    imei: Optional[str] = None
    etat_produit: Optional[dict] = None
    tests: Optional[dict] = None
    batterie_pourcentage: Optional[int] = None
    remarques: Optional[str] = None
    defauts_marks: Optional[List[dict]] = None
    piece_a_remplacer: Optional[str] = None
    offre_rachat: Optional[float] = None
    bon_pour_accord: Optional[bool] = None
    signature_data: Optional[str] = None


def serialize(r: dict) -> dict:
    r = dict(r)
    r["id"] = str(r["_id"])
    r.pop("_id", None)
    return r


async def next_number(prefix: str) -> str:
    year = datetime.now(timezone.utc).year
    key = f"{prefix}-{year}"
    counter = await db.counters.find_one_and_update(
        {"_id": key}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    return f"{prefix}-{year}-{counter['seq']:04d}"


@router.get("")
async def list_reprises(user: dict = Depends(get_current_user)):
    items = await db.reprises.find().sort("created_at", -1).to_list(2000)
    out = []
    for i in items:
        s = serialize(i)
        s["can_open"] = can_view_shop(user, i.get("shop_id"))
        out.append(s)
    return out


@router.get("/{item_id}")
async def get_reprise(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.reprises.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_view_shop(user, item.get("shop_id")):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    return serialize(item)


@router.post("")
async def create_reprise(payload: ReprisCreate, user: dict = Depends(get_current_user)):
    if not has_permission(user, "reprise", "create"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    numero = await next_number("REP")
    doc = payload.model_dump()
    doc["numero"] = numero
    doc["vendeur_id"] = user["_id"]
    doc["vendeur_nom"] = f"{user.get('prenom','')} {user.get('nom','')}"
    doc["date"] = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.reprises.insert_one(doc)
    created = await db.reprises.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.patch("/{item_id}")
async def update_reprise(item_id: str, payload: ReprisUpdate, user: dict = Depends(get_current_user)):
    if not has_permission(user, "reprise", "edit"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        await db.reprises.update_one({"_id": ObjectId(item_id)}, {"$set": update_data})
    updated = await db.reprises.find_one({"_id": ObjectId(item_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Introuvable")
    return serialize(updated)


@router.delete("/{item_id}")
async def delete_reprise(item_id: str, user: dict = Depends(get_current_user)):
    if not has_permission(user, "reprise", "delete"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    await db.reprises.delete_one({"_id": ObjectId(item_id)})
    return {"success": True}


@router.get("/{item_id}/pdf")
async def reprise_pdf(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.reprises.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    shop = await db.shops.find_one({"_id": ObjectId(item["shop_id"])}) or {}
    pdf_bytes = generate_reprise_pdf(item, shop)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename={item['numero']}.pdf"
    })
