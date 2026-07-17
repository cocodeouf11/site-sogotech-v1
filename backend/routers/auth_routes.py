import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel
from bson import ObjectId
from database import db
from auth_utils import verify_pin, create_access_token, get_current_user, hash_pin

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    pin: str


def serialize_user(user: dict) -> dict:
    user = dict(user)
    user["id"] = str(user["_id"])
    user.pop("_id", None)
    user.pop("pin_hash", None)
    return user


@router.post("/login")
async def login(payload: LoginRequest, response: Response):
    users = await db.users.find({"active": {"$ne": False}}).to_list(1000)
    matched = None
    for u in users:
        if verify_pin(payload.pin, u.get("pin_hash", "")):
            matched = u
            break
    if not matched:
        raise HTTPException(status_code=401, detail="Code PIN incorrect")
    token = create_access_token(str(matched["_id"]))
    response.set_cookie(key="access_token", value=token, httponly=True, secure=True, samesite="none", max_age=43200, path="/")
    return {"user": serialize_user(matched), "token": token}


@router.post("/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie("access_token", path="/")
    return {"success": True}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return serialize_user(user)
