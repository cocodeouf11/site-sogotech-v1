import os
import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import get_current_user, has_permission

router = APIRouter(prefix="/api/stock", tags=["stock"])
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(ROOT_DIR, os.environ.get("UPLOAD_DIR", "uploads"))


class ArticleCreate(BaseModel):
    nom: str
    quantite: int = 0
    categorie: Optional[str] = ""
    shop_id: Optional[str] = None
    prix: Optional[float] = 0


class ArticleUpdate(BaseModel):
    nom: Optional[str] = None
    quantite: Optional[int] = None
    categorie: Optional[str] = None
    prix: Optional[float] = None
    photo_url: Optional[str] = None


def serialize(a: dict) -> dict:
    a = dict(a)
    a["id"] = str(a["_id"])
    a.pop("_id", None)
    return a


@router.get("")
async def list_articles(user: dict = Depends(get_current_user)):
    articles = await db.articles.find().sort("nom", 1).to_list(5000)
    return [serialize(a) for a in articles]


@router.post("")
async def create_article(payload: ArticleCreate, user: dict = Depends(get_current_user)):
    if not has_permission(user, "stock", "add"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    doc = payload.model_dump()
    doc["photo_url"] = ""
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.articles.insert_one(doc)
    created = await db.articles.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.patch("/{article_id}")
async def update_article(article_id: str, payload: ArticleUpdate, user: dict = Depends(get_current_user)):
    update_data = payload.model_dump(exclude_unset=True)
    only_quantity = set(update_data.keys()) <= {"quantite"}
    if only_quantity:
        if not has_permission(user, "stock", "edit_quantity"):
            raise HTTPException(status_code=403, detail="Permission refusée")
    else:
        if not has_permission(user, "stock", "edit"):
            raise HTTPException(status_code=403, detail="Permission refusée")
    if update_data:
        await db.articles.update_one({"_id": ObjectId(article_id)}, {"$set": update_data})
    updated = await db.articles.find_one({"_id": ObjectId(article_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return serialize(updated)


@router.delete("/{article_id}")
async def delete_article(article_id: str, user: dict = Depends(get_current_user)):
    if not has_permission(user, "stock", "delete"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    await db.articles.delete_one({"_id": ObjectId(article_id)})
    return {"success": True}


@router.post("/{article_id}/photo")
async def upload_photo(article_id: str, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    if not has_permission(user, "stock", "edit"):
        raise HTTPException(status_code=403, detail="Permission refusée")
    os.makedirs(os.path.join(UPLOAD_DIR, "articles"), exist_ok=True)
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, "articles", filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    photo_url = f"/uploads/articles/{filename}"
    await db.articles.update_one({"_id": ObjectId(article_id)}, {"$set": {"photo_url": photo_url}})
    updated = await db.articles.find_one({"_id": ObjectId(article_id)})
    return serialize(updated)
