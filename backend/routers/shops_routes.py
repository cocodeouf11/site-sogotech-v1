import os
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import get_current_user, require_admin

router = APIRouter(prefix="/api/shops", tags=["shops"])
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(ROOT_DIR, os.environ.get("UPLOAD_DIR", "uploads"))


class ShopCreate(BaseModel):
    nom: str
    type: str
    adresse: Optional[str] = ""
    telephone: Optional[str] = ""
    siret: Optional[str] = ""


class ShopUpdate(BaseModel):
    nom: Optional[str] = None
    adresse: Optional[str] = None
    telephone: Optional[str] = None
    logo_url: Optional[str] = None
    siret: Optional[str] = None


def serialize(s: dict) -> dict:
    s = dict(s)
    s["id"] = str(s["_id"])
    s.pop("_id", None)
    return s


@router.get("")
async def list_shops(user: dict = Depends(get_current_user)):
    shops = await db.shops.find().sort("nom", 1).to_list(1000)
    return [serialize(s) for s in shops]


@router.post("")
async def create_shop(payload: ShopCreate, admin: dict = Depends(require_admin)):
    doc = payload.model_dump()
    doc["logo_url"] = ""
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.shops.insert_one(doc)
    created = await db.shops.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.patch("/{shop_id}")
async def update_shop(shop_id: str, payload: ShopUpdate, admin: dict = Depends(require_admin)):
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        await db.shops.update_one({"_id": ObjectId(shop_id)}, {"$set": update_data})
    updated = await db.shops.find_one({"_id": ObjectId(shop_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Boutique introuvable")
    return serialize(updated)


@router.delete("/{shop_id}")
async def delete_shop(shop_id: str, admin: dict = Depends(require_admin)):
    await db.shops.delete_one({"_id": ObjectId(shop_id)})
    return {"success": True}


@router.post("/{shop_id}/logo")
async def upload_logo(shop_id: str, file: UploadFile = File(...), admin: dict = Depends(require_admin)):
    os.makedirs(os.path.join(UPLOAD_DIR, "logos"), exist_ok=True)
    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, "logos", filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    logo_url = f"/uploads/logos/{filename}"
    await db.shops.update_one({"_id": ObjectId(shop_id)}, {"$set": {"logo_url": logo_url}})
    updated = await db.shops.find_one({"_id": ObjectId(shop_id)})
    return serialize(updated)
