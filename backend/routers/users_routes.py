from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, timezone
from database import db
from auth_utils import get_current_user, require_admin, hash_pin, is_admin
from constants import ALL_GRADES, GRADE_PERMISSION_TEMPLATES, DEFAULT_PERMISSIONS

router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    nom: str
    prenom: str
    poste: str
    grades: List[str]
    shop_id: Optional[str] = None
    telephone: Optional[str] = None
    pin: str
    is_admin: bool = False
    permissions: Optional[dict] = None


class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    poste: Optional[str] = None
    grades: Optional[List[str]] = None
    shop_id: Optional[str] = None
    telephone: Optional[str] = None
    pin: Optional[str] = None
    active: Optional[bool] = None
    permissions: Optional[dict] = None


def serialize(u: dict) -> dict:
    u = dict(u)
    u["id"] = str(u["_id"])
    u.pop("_id", None)
    u.pop("pin_hash", None)
    return u


def build_permissions(grades: List[str], override: Optional[dict]) -> dict:
    merged = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT_PERMISSIONS.items()}
    for g in grades:
        template = GRADE_PERMISSION_TEMPLATES.get(g)
        if not template:
            continue
        for module, val in template.items():
            if isinstance(val, dict):
                for action, allowed in val.items():
                    if allowed:
                        merged[module][action] = True
            else:
                merged[module] = merged[module] or val
    if override:
        for module, val in override.items():
            if module not in merged:
                continue
            if isinstance(val, dict):
                merged[module].update(val)
            else:
                merged[module] = val
    return merged


@router.get("/grades")
async def get_grades(user: dict = Depends(get_current_user)):
    return {"grades": ALL_GRADES}


@router.get("")
async def list_users(user: dict = Depends(get_current_user)):
    users = await db.users.find().sort("nom", 1).to_list(1000)
    return [serialize(u) for u in users]


@router.post("")
async def create_user(payload: UserCreate, admin: dict = Depends(require_admin)):
    if len(payload.pin) != 6 or not payload.pin.isdigit():
        raise HTTPException(status_code=400, detail="Le code PIN doit contenir exactement 6 chiffres")
    doc = payload.model_dump(exclude={"pin"})
    doc["pin_hash"] = hash_pin(payload.pin)
    doc["permissions"] = build_permissions(payload.grades, payload.permissions)
    doc["active"] = True
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.users.insert_one(doc)
    created = await db.users.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.patch("/{user_id}")
async def update_user(user_id: str, payload: UserUpdate, admin: dict = Depends(require_admin)):
    existing = await db.users.find_one({"_id": ObjectId(user_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    update_data = payload.model_dump(exclude_unset=True, exclude={"pin"})
    if payload.pin:
        if len(payload.pin) != 6 or not payload.pin.isdigit():
            raise HTTPException(status_code=400, detail="Le code PIN doit contenir exactement 6 chiffres")
        update_data["pin_hash"] = hash_pin(payload.pin)
    if "permissions" in update_data or "grades" in update_data:
        grades = update_data.get("grades", existing.get("grades", []))
        override = update_data.get("permissions", existing.get("permissions"))
        update_data["permissions"] = build_permissions(grades, override)
    if update_data:
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    updated = await db.users.find_one({"_id": ObjectId(user_id)})
    return serialize(updated)


@router.delete("/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    await db.users.delete_one({"_id": ObjectId(user_id)})
    return {"success": True}
