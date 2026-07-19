from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException
from pydantic import BaseModel
from database import db
from auth_utils import effective_shop_id


class ShareRequest(BaseModel):
    user_id: str
    mode: str = "read"


def find_share_entry(item: dict, user_id: str) -> Optional[dict]:
    for s in (item.get("shared_with") or []):
        if s.get("user_id") == user_id:
            return s
    return None


def document_visibility_query(user: dict) -> dict:
    """Query filter for list endpoints: own effective shop's documents, plus
    anything explicitly shared with this user (regardless of shop)."""
    return {"$or": [{"shop_id": effective_shop_id(user)}, {"shared_with.user_id": user["_id"]}]}


def can_access_document(user: dict, item: dict) -> Optional[dict]:
    """Returns access info if the user may view this document, else None.
    {"owner": True} if it belongs to the user's active shop.
    {"owner": False, "mode": "read"|"write"} if accessed via a share."""
    if item.get("shop_id") == effective_shop_id(user):
        return {"owner": True}
    entry = find_share_entry(item, user["_id"])
    if entry:
        return {"owner": False, "mode": entry.get("mode")}
    return None


def annotate_share(serialized: dict, item: dict, user: dict) -> dict:
    access = can_access_document(user, item)
    serialized["can_open"] = True
    if access and not access["owner"]:
        entry = find_share_entry(item, user["_id"])
        serialized["is_shared_to_me"] = True
        serialized["share_mode"] = entry.get("mode")
        label = f"{entry.get('shared_by_shop_name', '')} - {entry.get('shared_by_name', '')}".strip(" -")
        serialized["shared_by_label"] = label
    else:
        serialized["is_shared_to_me"] = False
        serialized["share_mode"] = None
        serialized["shared_by_label"] = None
    return serialized


async def share_document(collection, item_id: str, payload: ShareRequest, user: dict, has_share_permission: bool):
    if not has_share_permission:
        raise HTTPException(status_code=403, detail="Permission de partage refusée")
    if payload.mode not in ("read", "write"):
        raise HTTPException(status_code=400, detail="Mode invalide (lecture ou lecture/écriture)")
    item = await collection.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Introuvable")
    eff = effective_shop_id(user)
    if item.get("shop_id") != eff:
        raise HTTPException(status_code=403, detail="Vous ne pouvez partager que les documents de votre boutique")
    target = await db.users.find_one({"_id": ObjectId(payload.user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur cible introuvable")
    shop = await db.shops.find_one({"_id": ObjectId(eff)}) if eff else None
    entry = {
        "user_id": str(target["_id"]),
        "mode": payload.mode,
        "shared_by_user_id": user["_id"],
        "shared_by_name": f"{user.get('prenom', '')} {user.get('nom', '')}".strip(),
        "shared_by_shop_name": (shop or {}).get("nom", ""),
        "shared_at": datetime.now(timezone.utc).isoformat(),
    }
    shares = [s for s in (item.get("shared_with") or []) if s.get("user_id") != entry["user_id"]]
    shares.append(entry)
    await collection.update_one({"_id": ObjectId(item_id)}, {"$set": {"shared_with": shares}})
    return {"success": True}
