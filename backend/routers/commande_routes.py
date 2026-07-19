import re
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import get_current_user, has_permission, is_admin
from routers.stock_routes import next_article_code

router = APIRouter(prefix="/api/commandes", tags=["commandes"])


class NonConformeItem(BaseModel):
    line_id: str
    description: str
    note: str = ""


class ResolveNonConforme(BaseModel):
    items: List[NonConformeItem]
    description: str = ""


def serialize(c: dict, user: dict) -> dict:
    c = dict(c)
    c["id"] = str(c["_id"])
    c.pop("_id", None)
    if not has_permission(user, "depot", "access"):
        c.pop("notification_message", None)
    return c


def can_view(user: dict, commande: dict) -> bool:
    if is_admin(user) or has_permission(user, "depot", "access"):
        return True
    return user.get("shop_id") == commande.get("shop_id")


def can_resolve(user: dict, commande: dict) -> bool:
    return is_admin(user) or user.get("shop_id") == commande.get("shop_id")


@router.get("")
async def list_commandes(user: dict = Depends(get_current_user)):
    if is_admin(user) or has_permission(user, "depot", "access"):
        query = {}
    else:
        query = {"shop_id": user.get("shop_id")}
    items = await db.commandes.find(query).sort("created_at", -1).to_list(2000)
    return [serialize(c, user) for c in items]


@router.get("/{commande_id}")
async def get_commande(commande_id: str, user: dict = Depends(get_current_user)):
    commande = await db.commandes.find_one({"_id": ObjectId(commande_id)})
    if not commande:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_view(user, commande):
        raise HTTPException(status_code=403, detail="Accès restreint à cette boutique")
    return serialize(commande, user)


@router.post("/{commande_id}/resolve-conforme")
async def resolve_conforme(commande_id: str, user: dict = Depends(get_current_user)):
    commande = await db.commandes.find_one({"_id": ObjectId(commande_id)})
    if not commande:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_resolve(user, commande):
        raise HTTPException(status_code=403, detail="Seule la boutique destinataire peut valider cette commande")
    if commande.get("status") != "envoyee":
        raise HTTPException(status_code=400, detail="Cette commande a déjà été traitée")

    for line in commande.get("lines", []):
        nom = line.get("description", "").strip()
        if not nom:
            continue
        qty = line.get("quantite_attendue", 0)
        existing = await db.articles.find_one({
            "shop_id": commande["shop_id"],
            "nom": {"$regex": f"^{re.escape(nom)}$", "$options": "i"},
        })
        if existing:
            await db.articles.update_one({"_id": existing["_id"]}, {"$inc": {"quantite": qty}})
        else:
            code = line.get("ugs") or await next_article_code()
            dup = await db.articles.find_one({"code": code})
            if dup:
                code = await next_article_code()
            await db.articles.insert_one({
                "nom": nom,
                "quantite": qty,
                "categorie": "",
                "prix": 0,
                "shop_id": commande["shop_id"],
                "code": code,
                "photo_url": "",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

    notification_message = f"{commande.get('shop_nom')} a validé la commande {commande.get('numero')} : tous les articles ont été ajoutés au stock."
    await db.commandes.update_one({"_id": ObjectId(commande_id)}, {"$set": {
        "status": "conforme",
        "resolved_by": user["_id"],
        "resolved_by_nom": f"{user.get('prenom','')} {user.get('nom','')}",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "notification_message": notification_message,
    }})
    updated = await db.commandes.find_one({"_id": ObjectId(commande_id)})
    return serialize(updated, user)


@router.post("/{commande_id}/resolve-non-conforme")
async def resolve_non_conforme(commande_id: str, payload: ResolveNonConforme, user: dict = Depends(get_current_user)):
    commande = await db.commandes.find_one({"_id": ObjectId(commande_id)})
    if not commande:
        raise HTTPException(status_code=404, detail="Introuvable")
    if not can_resolve(user, commande):
        raise HTTPException(status_code=403, detail="Seule la boutique destinataire peut valider cette commande")
    if commande.get("status") != "envoyee":
        raise HTTPException(status_code=400, detail="Cette commande a déjà été traitée")

    items = [i.model_dump() for i in payload.items]
    notification_message = f"{commande.get('shop_nom')} a signalé un problème sur la commande {commande.get('numero')} ({len(items)} article(s)) : {payload.description}"
    await db.commandes.update_one({"_id": ObjectId(commande_id)}, {"$set": {
        "status": "non_conforme",
        "non_conforme_items": items,
        "resolution_note": payload.description,
        "resolved_by": user["_id"],
        "resolved_by_nom": f"{user.get('prenom','')} {user.get('nom','')}",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "notification_message": notification_message,
    }})
    updated = await db.commandes.find_one({"_id": ObjectId(commande_id)})
    return serialize(updated, user)
