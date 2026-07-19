from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import get_current_user, has_permission, effective_shop_id
from sharing_utils import ShareRequest, share_document, document_visibility_query, annotate_share, can_access_document
from pdf_utils import generate_devis_pdf

router = APIRouter(prefix="/api/devis", tags=["devis"])

DEFAULT_MENTIONS = (
    "Devis valable 30 jours à compter de sa date d'émission. Ce devis ne constitue pas une facture. "
    "Tout travail supplémentaire non prévu fera l'objet d'un devis complémentaire."
)


class DevisItem(BaseModel):
    nom: str
    prix_unitaire: float
    quantite: float = 1


class DevisCreate(BaseModel):
    shop_id: str
    client_nom: str
    client_tel: Optional[str] = ""
    client_email: Optional[str] = ""
    items: List[DevisItem] = []
    intervention_ids: List[str] = []
    mentions_legales: Optional[str] = DEFAULT_MENTIONS
    signature_data: Optional[str] = ""


class DevisUpdate(BaseModel):
    numero: Optional[str] = None
    client_nom: Optional[str] = None
    client_tel: Optional[str] = None
    client_email: Optional[str] = None
    items: Optional[List[DevisItem]] = None
    intervention_ids: Optional[List[str]] = None
    mentions_legales: Optional[str] = None
    signature_data: Optional[str] = None
    status: Optional[str] = None


def serialize(d: dict) -> dict:
    d = dict(d)
    d["id"] = str(d["_id"])
    d.pop("_id", None)
    return d


async def next_number(prefix: str) -> str:
    year = datetime.now(timezone.utc).year
    key = f"{prefix}-{year}"
    counter = await db.counters.find_one_and_update(
        {"_id": key}, {"$inc": {"seq": 1}}, upsert=True, return_document=True
    )
    return f"{prefix}-{year}-{counter['seq']:04d}"


@router.get("")
async def list_devis(user: dict = Depends(get_current_user)):
    items = await db.devis.find(document_visibility_query(user)).sort("created_at", -1).to_list(2000)
    return [annotate_share(serialize(i), i, user) for i in items]


@router.get("/{item_id}")
async def get_devis(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.devis.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_access_document(user, item):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    return annotate_share(serialize(item), item, user)


@router.post("")
async def create_devis(payload: DevisCreate, user: dict = Depends(get_current_user)):
    if not has_permission(user, "devis", "create"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    eff = effective_shop_id(user)
    if not eff:
        raise HTTPException(status_code=400, detail="Veuillez sélectionner une boutique de travail")
    numero = await next_number("DEV")
    doc = payload.model_dump()
    doc["items"] = [i for i in doc["items"]]
    doc["shop_id"] = eff
    doc["numero"] = numero
    doc["vendeur_id"] = user["_id"]
    doc["vendeur_nom"] = f"{user.get('prenom','')} {user.get('nom','')}"
    doc["date"] = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    doc["status"] = "brouillon"
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.devis.insert_one(doc)
    created = await db.devis.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.patch("/{item_id}")
async def update_devis(item_id: str, payload: DevisUpdate, user: dict = Depends(get_current_user)):
    item = await db.devis.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    access = can_access_document(user, item)
    if not access:
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    if access["owner"]:
        if not has_permission(user, "devis", "edit"):
            raise HTTPException(status_code=403, detail="Permission refusée")
    elif access["mode"] != "write":
        raise HTTPException(status_code=403, detail="Document partagé en lecture seule")
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        await db.devis.update_one({"_id": ObjectId(item_id)}, {"$set": update_data})
    updated = await db.devis.find_one({"_id": ObjectId(item_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Introuvable")
    return serialize(updated)


@router.delete("/{item_id}")
async def delete_devis(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.devis.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    if item.get("shop_id") != effective_shop_id(user):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    if not has_permission(user, "devis", "delete"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    await db.devis.delete_one({"_id": ObjectId(item_id)})
    return {"success": True}


@router.post("/{item_id}/share")
async def share_devis(item_id: str, payload: ShareRequest, user: dict = Depends(get_current_user)):
    return await share_document(db.devis, item_id, payload, user, has_permission(user, "partage_document", "share"))


@router.get("/{item_id}/pdf")
async def devis_pdf(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.devis.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_access_document(user, item):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    shop = await db.shops.find_one({"_id": ObjectId(item["shop_id"])}) or {}
    pdf_bytes = generate_devis_pdf(item, shop)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename={item['numero']}.pdf"
    })
