from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import get_current_user, has_permission, effective_shop_id
from sharing_utils import ShareRequest, share_document, document_visibility_query, annotate_share, can_access_document
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
    items = await db.reprises.find(document_visibility_query(user)).sort("created_at", -1).to_list(2000)
    return [annotate_share(serialize(i), i, user) for i in items]


@router.get("/{item_id}")
async def get_reprise(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.reprises.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_access_document(user, item):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    return annotate_share(serialize(item), item, user)


@router.post("")
async def create_reprise(payload: ReprisCreate, user: dict = Depends(get_current_user)):
    if not has_permission(user, "reprise", "create"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    eff = effective_shop_id(user)
    if not eff:
        raise HTTPException(status_code=400, detail="Veuillez sélectionner une boutique de travail")
    numero = await next_number("REP")
    doc = payload.model_dump()
    doc["shop_id"] = eff
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
    item = await db.reprises.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    access = can_access_document(user, item)
    if not access:
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    if access["owner"]:
        if not has_permission(user, "reprise", "edit"):
            raise HTTPException(status_code=403, detail="Permission refusée")
    elif access["mode"] != "write":
        raise HTTPException(status_code=403, detail="Document partagé en lecture seule")
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        await db.reprises.update_one({"_id": ObjectId(item_id)}, {"$set": update_data})
    updated = await db.reprises.find_one({"_id": ObjectId(item_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Introuvable")
    return serialize(updated)


@router.delete("/{item_id}")
async def delete_reprise(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.reprises.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    if item.get("shop_id") != effective_shop_id(user):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    if not has_permission(user, "reprise", "delete"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    await db.reprises.delete_one({"_id": ObjectId(item_id)})
    return {"success": True}


@router.post("/{item_id}/share")
async def share_reprise(item_id: str, payload: ShareRequest, user: dict = Depends(get_current_user)):
    return await share_document(db.reprises, item_id, payload, user, has_permission(user, "partage_document", "share"))


@router.get("/{item_id}/pdf")
async def reprise_pdf(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.reprises.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_access_document(user, item):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    shop = await db.shops.find_one({"_id": ObjectId(item["shop_id"])}) or {}
    pdf_bytes = generate_reprise_pdf(item, shop)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename={item['numero']}.pdf"
    })
