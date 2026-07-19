import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from database import db, client
from auth_utils import hash_pin, verify_pin
from constants import GRADE_PERMISSION_TEMPLATES, DEFAULT_PERMISSIONS
from routers import (
    auth_routes,
    users_routes,
    shops_routes,
    stock_routes,
    caisse_routes,
    intervention_routes,
    devis_routes,
    reprise_routes,
    communication_routes,
    depot_routes,
    commande_routes,
)

app = FastAPI()
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "Boutique/Dépôt API"}


app.include_router(api_router)
app.include_router(auth_routes.router)
app.include_router(users_routes.router)
app.include_router(shops_routes.router)
app.include_router(stock_routes.router)
app.include_router(caisse_routes.router)
app.include_router(intervention_routes.router)
app.include_router(devis_routes.router)
app.include_router(reprise_routes.router)
app.include_router(communication_routes.router)
app.include_router(depot_routes.router)
app.include_router(commande_routes.router)

upload_dir = os.path.join(str(ROOT_DIR), os.environ.get("UPLOAD_DIR", "uploads"))
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def seed_data():
    await db.users.create_index("nom")
    await db.articles.create_index("nom")

    shop = await db.shops.find_one({"type": "boutique"})
    if not shop:
        result = await db.shops.insert_one({
            "nom": "Boutique Centrale",
            "type": "boutique",
            "adresse": "12 Rue de la République, 75001 Paris",
            "telephone": "01 23 45 67 89",
            "logo_url": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        shop_id = str(result.inserted_id)
    else:
        shop_id = str(shop["_id"])

    depot = await db.shops.find_one({"type": "depot"})
    if not depot:
        await db.shops.insert_one({
            "nom": "Dépôt Central",
            "type": "depot",
            "adresse": "5 Zone Industrielle, 93000 Bobigny",
            "telephone": "01 98 76 54 32",
            "logo_url": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    admin = await db.users.find_one({"is_admin": True})
    admin_pin = os.environ.get("ADMIN_PIN", "123456")
    if not admin:
        await db.users.insert_one({
            "nom": "Admin",
            "prenom": "Super",
            "poste": "Administrateur",
            "grades": ["Gestionnaire toutes boutiques"],
            "shop_id": shop_id,
            "telephone": "",
            "pin_hash": hash_pin(admin_pin),
            "is_admin": True,
            "active": True,
            "permissions": GRADE_PERMISSION_TEMPLATES["Gestionnaire toutes boutiques"],
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info("Admin seeded with PIN from ADMIN_PIN env var")
    elif not verify_pin(admin_pin, admin.get("pin_hash", "")):
        await db.users.update_one({"_id": admin["_id"]}, {"$set": {"pin_hash": hash_pin(admin_pin)}})
        logger.info("Admin PIN updated to match ADMIN_PIN env var")

    async for u in db.users.find({"permissions.depot": {"$exists": False}}):
        grades = u.get("grades") or []
        depot_allowed = any(GRADE_PERMISSION_TEMPLATES.get(g, {}).get("depot") for g in grades)
        await db.users.update_one({"_id": u["_id"]}, {"$set": {"permissions.depot": depot_allowed}})

    await db.articles.update_many({"shop_id": {"$in": [None, ""]}}, {"$set": {"shop_id": shop_id}})


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
