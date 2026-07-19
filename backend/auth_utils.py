import os
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, Depends
from database import db

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_HOURS = 12


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_pin(pin: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_HOURS),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token invalide")
        user = await db.users.find_one({"_id": __import__("bson").ObjectId(payload["sub"])})
        if not user or not user.get("active", True):
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")
        user["_id"] = str(user["_id"])
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expirée")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")


def is_admin(user: dict) -> bool:
    return user.get("is_admin", False)


def is_all_shops_manager(user: dict) -> bool:
    return "Gestionnaire toutes boutiques" in (user.get("grades") or [])


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Accès réservé à l'administrateur")
    return user


def has_permission(user: dict, module: str, action: str) -> bool:
    if is_admin(user):
        return True
    perms = user.get("permissions") or {}
    module_perms = perms.get(module) or {}
    if isinstance(module_perms, bool):
        return module_perms
    return bool(module_perms.get(action, False))


def is_multi_shop_user(user: dict) -> bool:
    """Admin, Gestionnaire toutes boutiques, or a user granted the 'inter_boutique'
    permission must pick an active shop context (they don't see a merged view anymore)."""
    if is_admin(user) or is_all_shops_manager(user):
        return True
    return has_permission(user, "inter_boutique", "access")


def effective_shop_id(user: dict):
    """The shop a user is currently allowed to read/write data for.
    - Regular users: always their own assigned shop.
    - Multi-shop users: the shop they explicitly selected (active_shop_id), or None
      if they haven't picked one yet (frontend must force the selector in that case)."""
    if is_multi_shop_user(user):
        return user.get("active_shop_id")
    return user.get("shop_id")


def enrich_user(user: dict) -> dict:
    user = dict(user)
    user["is_multi_shop_user"] = is_multi_shop_user(user)
    user["effective_shop_id"] = effective_shop_id(user)
    return user
