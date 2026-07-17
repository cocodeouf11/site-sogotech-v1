import os
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import get_current_user

router = APIRouter(prefix="/api/communication", tags=["communication"])
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(ROOT_DIR, os.environ.get("UPLOAD_DIR", "uploads"))


class MessageCreate(BaseModel):
    to_user_id: str
    content: str


class HelpTicketCreate(BaseModel):
    subject: str
    description: str
    urgence: str = "moyenne"


class HelpTicketUpdate(BaseModel):
    status: Optional[str] = None
    urgence: Optional[str] = None
    assigned_to: Optional[str] = None


class CommentCreate(BaseModel):
    content: str


def serialize(d: dict) -> dict:
    d = dict(d)
    d["id"] = str(d["_id"])
    d.pop("_id", None)
    return d


@router.get("/messages")
async def list_messages(with_user: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"$or": [{"from_user_id": user["_id"]}, {"to_user_id": user["_id"]}]}
    if with_user:
        query = {"$or": [
            {"from_user_id": user["_id"], "to_user_id": with_user},
            {"from_user_id": with_user, "to_user_id": user["_id"]},
        ]}
    messages = await db.messages.find(query).sort("created_at", 1).to_list(2000)
    return [serialize(m) for m in messages]


@router.post("/messages")
async def send_message(payload: MessageCreate, user: dict = Depends(get_current_user)):
    doc = {
        "from_user_id": user["_id"],
        "from_user_nom": f"{user.get('prenom','')} {user.get('nom','')}",
        "to_user_id": payload.to_user_id,
        "content": payload.content,
        "attachment_url": "",
        "attachment_name": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.messages.insert_one(doc)
    created = await db.messages.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.post("/messages/attachment")
async def send_attachment(to_user_id: str = Form(...), file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    os.makedirs(os.path.join(UPLOAD_DIR, "attachments"), exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, "attachments", filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    doc = {
        "from_user_id": user["_id"],
        "from_user_nom": f"{user.get('prenom','')} {user.get('nom','')}",
        "to_user_id": to_user_id,
        "content": "",
        "attachment_url": f"/uploads/attachments/{filename}",
        "attachment_name": file.filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.messages.insert_one(doc)
    created = await db.messages.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.get("/tickets")
async def list_help_tickets(user: dict = Depends(get_current_user)):
    tickets = await db.help_tickets.find().sort("created_at", -1).to_list(2000)
    return [serialize(t) for t in tickets]


@router.post("/tickets")
async def create_help_ticket(payload: HelpTicketCreate, user: dict = Depends(get_current_user)):
    doc = payload.model_dump()
    doc["created_by"] = user["_id"]
    doc["created_by_nom"] = f"{user.get('prenom','')} {user.get('nom','')}"
    doc["status"] = "ouvert"
    doc["assigned_to"] = None
    doc["comments"] = []
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.help_tickets.insert_one(doc)
    created = await db.help_tickets.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.patch("/tickets/{ticket_id}")
async def update_help_ticket(ticket_id: str, payload: HelpTicketUpdate, user: dict = Depends(get_current_user)):
    update_data = payload.model_dump(exclude_unset=True)
    if update_data:
        await db.help_tickets.update_one({"_id": ObjectId(ticket_id)}, {"$set": update_data})
    updated = await db.help_tickets.find_one({"_id": ObjectId(ticket_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Introuvable")
    return serialize(updated)


@router.post("/tickets/{ticket_id}/comments")
async def add_comment(ticket_id: str, payload: CommentCreate, user: dict = Depends(get_current_user)):
    comment = {
        "author": f"{user.get('prenom','')} {user.get('nom','')}",
        "content": payload.content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.help_tickets.update_one({"_id": ObjectId(ticket_id)}, {"$push": {"comments": comment}})
    updated = await db.help_tickets.find_one({"_id": ObjectId(ticket_id)})
    if not updated:
        raise HTTPException(status_code=404, detail="Introuvable")
    return serialize(updated)
