import os
import re
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Form
from pydantic import BaseModel
from bson import ObjectId
import fitz
from database import db
from auth_utils import get_current_user

router = APIRouter(prefix="/api/depot", tags=["depot"])
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(ROOT_DIR, os.environ.get("UPLOAD_DIR", "uploads"))
LINE_PATTERN = re.compile(r"^(?P<name>.{3,60}?)\s+(?P<qty>\d{1,4})\s*$")


class LineUpdate(BaseModel):
    delta: Optional[int] = None
    reset: Optional[bool] = None


class LineCreate(BaseModel):
    description: str
    quantite_attendue: int = 1


def serialize(o: dict) -> dict:
    o = dict(o)
    o["id"] = str(o["_id"])
    o.pop("_id", None)
    return o


def parse_delivery_lines(pdf_path: str) -> List[dict]:
    lines = []
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text = page.get_text()
            for raw_line in text.split("\n"):
                match = LINE_PATTERN.match(raw_line.strip())
                if match:
                    lines.append({
                        "id": str(uuid.uuid4()),
                        "description": match.group("name").strip(),
                        "quantite_attendue": int(match.group("qty")),
                        "quantite_picked": 0,
                    })
        doc.close()
    except Exception:
        pass
    return lines


@router.get("/orders")
async def list_orders(q: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if q:
        query["numero"] = {"$regex": q, "$options": "i"}
    orders = await db.depot_orders.find(query).sort("created_at", -1).to_list(2000)
    return [serialize(o) for o in orders]


@router.get("/orders/{order_id}")
async def get_order(order_id: str, user: dict = Depends(get_current_user)):
    order = await db.depot_orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Introuvable")
    return serialize(order)


@router.post("/orders")
async def create_order(numero: str = Form(...), delivery: UploadFile = File(...), label: Optional[UploadFile] = File(None), user: dict = Depends(get_current_user)):
    os.makedirs(os.path.join(UPLOAD_DIR, "depot"), exist_ok=True)
    delivery_filename = f"{uuid.uuid4()}.pdf"
    delivery_path = os.path.join(UPLOAD_DIR, "depot", delivery_filename)
    content = await delivery.read()
    with open(delivery_path, "wb") as f:
        f.write(content)

    label_url = ""
    if label:
        label_filename = f"{uuid.uuid4()}.pdf"
        label_path = os.path.join(UPLOAD_DIR, "depot", label_filename)
        label_content = await label.read()
        with open(label_path, "wb") as f:
            f.write(label_content)
        label_url = f"/uploads/depot/{label_filename}"

    lines = parse_delivery_lines(delivery_path)
    doc = {
        "numero": numero,
        "delivery_pdf_url": f"/uploads/depot/{delivery_filename}",
        "label_pdf_url": label_url,
        "lines": lines,
        "status": "en_attente",
        "created_by": user["_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.depot_orders.insert_one(doc)
    created = await db.depot_orders.find_one({"_id": result.inserted_id})
    return serialize(created)


@router.post("/orders/{order_id}/lines")
async def add_line(order_id: str, payload: LineCreate, user: dict = Depends(get_current_user)):
    line = {"id": str(uuid.uuid4()), "description": payload.description, "quantite_attendue": payload.quantite_attendue, "quantite_picked": 0}
    await db.depot_orders.update_one({"_id": ObjectId(order_id)}, {"$push": {"lines": line}})
    updated = await db.depot_orders.find_one({"_id": ObjectId(order_id)})
    return serialize(updated)


@router.post("/orders/{order_id}/lines/{line_id}/increment")
async def increment_line(order_id: str, line_id: str, payload: LineUpdate, user: dict = Depends(get_current_user)):
    order = await db.depot_orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Introuvable")
    lines = order.get("lines", [])
    for line in lines:
        if line["id"] == line_id:
            if payload.reset:
                line["quantite_picked"] = 0
            else:
                line["quantite_picked"] = max(0, line.get("quantite_picked", 0) + (payload.delta or 1))
    all_done = all(l.get("quantite_picked", 0) >= l.get("quantite_attendue", 0) for l in lines) if lines else False
    status = "termine" if all_done else "en_cours"
    await db.depot_orders.update_one({"_id": ObjectId(order_id)}, {"$set": {"lines": lines, "status": status}})
    updated = await db.depot_orders.find_one({"_id": ObjectId(order_id)})
    return serialize(updated)


@router.delete("/orders/{order_id}")
async def delete_order(order_id: str, user: dict = Depends(get_current_user)):
    await db.depot_orders.delete_one({"_id": ObjectId(order_id)})
    return {"success": True}
