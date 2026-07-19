#!/usr/bin/env python3
"""
Migration / synchronisation MongoDB -> MariaDB pour SOGO Gestion.

Ce script est un outil de RÉPLICATION ponctuelle ou périodique (cron) des
données de l'application (qui tourne sur MongoDB) vers une base MariaDB
utilisée pour le reporting, la sauvegarde ou l'interopérabilité avec
d'autres outils. Il ne remplace PAS MongoDB : l'application continue de
lire/écrire dans MongoDB.

Chaque exécution vide puis ré-insère chaque table (synchronisation complète,
idempotente). Adapté à un usage quotidien via cron sur des volumes de
données de PME (quelques dizaines de milliers de documents).

Variables d'environnement attendues (voir .env.example dans ce dossier) :
  MONGO_URL, DB_NAME            -> connexion MongoDB (mêmes valeurs que backend/.env)
  MARIADB_HOST, MARIADB_PORT, MARIADB_USER, MARIADB_PASSWORD, MARIADB_DATABASE

Utilisation :
  pip install -r requirements.txt
  python3 migrate_mongo_to_mariadb.py
"""
import os
import json
from datetime import datetime, timezone

import pymongo
import pymysql

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
MARIADB_HOST = os.environ["MARIADB_HOST"]
MARIADB_PORT = int(os.environ.get("MARIADB_PORT", "3306"))
MARIADB_USER = os.environ["MARIADB_USER"]
MARIADB_PASSWORD = os.environ["MARIADB_PASSWORD"]
MARIADB_DATABASE = os.environ["MARIADB_DATABASE"]


def parse_dt(value):
    """Convertit une date ISO string Mongo en datetime naïf UTC pour MariaDB."""
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value))
        except ValueError:
            return None
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def js(value):
    """Sérialise une structure Mongo (liste/dict) en JSON pour une colonne JSON."""
    if value is None:
        return None
    return json.dumps(value, default=str, ensure_ascii=False)


def oid(value):
    return str(value) if value is not None else None


# Mapping: (collection Mongo, table MariaDB, fonction de conversion doc -> tuple de valeurs, colonnes SQL)
def build_table_specs():
    return [
        ("shops", "shops",
         ["id", "nom", "type", "adresse", "telephone", "siret", "logo_url", "created_at"],
         lambda d: (oid(d["_id"]), d.get("nom"), d.get("type"), d.get("adresse"), d.get("telephone"),
                    d.get("siret"), d.get("logo_url"), parse_dt(d.get("created_at")))),

        ("users", "users",
         ["id", "nom", "prenom", "poste", "grades", "shop_id", "active_shop_id", "telephone",
          "is_admin", "active", "permissions", "created_at"],
         lambda d: (oid(d["_id"]), d.get("nom"), d.get("prenom"), d.get("poste"), js(d.get("grades")),
                    d.get("shop_id"), d.get("active_shop_id"), d.get("telephone"),
                    bool(d.get("is_admin", False)), bool(d.get("active", True)),
                    js(d.get("permissions")), parse_dt(d.get("created_at")))),

        ("articles", "articles",
         ["id", "code", "nom", "quantite", "categorie", "prix", "photo_url", "shop_id", "created_at"],
         lambda d: (oid(d["_id"]), d.get("code"), d.get("nom"), d.get("quantite", 0), d.get("categorie"),
                    d.get("prix", 0), d.get("photo_url"), d.get("shop_id"), parse_dt(d.get("created_at")))),

        ("tickets", "tickets",
         ["id", "type", "numero", "shop_id", "vendeur_id", "vendeur_nom", "doc_date", "items",
          "tva_percent", "total_ht", "total_tva", "total_ttc", "client_info", "shared_with", "created_at"],
         lambda d: (oid(d["_id"]), d.get("type"), d.get("numero"), d.get("shop_id"), d.get("vendeur_id"),
                    d.get("vendeur_nom"), d.get("date"), js(d.get("items")), d.get("tva_percent"),
                    d.get("total_ht"), d.get("total_tva"), d.get("total_ttc"), js(d.get("client_info")),
                    js(d.get("shared_with")), parse_dt(d.get("created_at")))),

        ("interventions", "interventions",
         ["id", "numero", "shop_id", "client_nom", "client_tel", "client_email", "client_adresse",
          "materiel", "imei", "motif", "intervention_effectuee", "signature_data", "vendeur_id",
          "vendeur_nom", "doc_date", "shared_with", "created_at"],
         lambda d: (oid(d["_id"]), d.get("numero"), d.get("shop_id"), d.get("client_nom"), d.get("client_tel"),
                    d.get("client_email"), d.get("client_adresse"), d.get("materiel"), d.get("imei"),
                    d.get("motif"), d.get("intervention_effectuee"), d.get("signature_data"),
                    d.get("vendeur_id"), d.get("vendeur_nom"), d.get("date"), js(d.get("shared_with")),
                    parse_dt(d.get("created_at")))),

        ("devis", "devis",
         ["id", "numero", "shop_id", "client_nom", "client_tel", "client_email", "items",
          "intervention_ids", "mentions_legales", "signature_data", "vendeur_id", "vendeur_nom",
          "doc_date", "status", "shared_with", "created_at"],
         lambda d: (oid(d["_id"]), d.get("numero"), d.get("shop_id"), d.get("client_nom"), d.get("client_tel"),
                    d.get("client_email"), js(d.get("items")), js(d.get("intervention_ids")),
                    d.get("mentions_legales"), d.get("signature_data"), d.get("vendeur_id"),
                    d.get("vendeur_nom"), d.get("date"), d.get("status"), js(d.get("shared_with")),
                    parse_dt(d.get("created_at")))),

        ("reprises", "reprises",
         ["id", "numero", "shop_id", "client_nom", "client_tel", "client_email", "client_adresse",
          "modele", "capacite", "imei", "etat_produit", "tests", "batterie_pourcentage", "remarques",
          "defauts_marks", "piece_a_remplacer", "offre_rachat", "bon_pour_accord", "signature_data",
          "vendeur_id", "vendeur_nom", "doc_date", "shared_with", "created_at"],
         lambda d: (oid(d["_id"]), d.get("numero"), d.get("shop_id"), d.get("client_nom"), d.get("client_tel"),
                    d.get("client_email"), d.get("client_adresse"), d.get("modele"), d.get("capacite"),
                    d.get("imei"), js(d.get("etat_produit")), js(d.get("tests")),
                    d.get("batterie_pourcentage"), d.get("remarques"), js(d.get("defauts_marks")),
                    d.get("piece_a_remplacer"), d.get("offre_rachat"), bool(d.get("bon_pour_accord", False)),
                    d.get("signature_data"), d.get("vendeur_id"), d.get("vendeur_nom"), d.get("date"),
                    js(d.get("shared_with")), parse_dt(d.get("created_at")))),

        ("depot_orders", "depot_orders",
         ["id", "numero", "delivery_pdf_url", "label_pdf_url", "`lines`", "status", "created_by", "created_at"],
         lambda d: (oid(d["_id"]), d.get("numero"), d.get("delivery_pdf_url"), d.get("label_pdf_url"),
                    js(d.get("lines")), d.get("status"), d.get("created_by"), parse_dt(d.get("created_at")))),

        ("commandes", "commandes",
         ["id", "numero", "depot_order_id", "shop_id", "shop_nom", "`lines`", "delivery_pdf_url", "status",
          "non_conforme_items", "resolution_note", "notification_message", "sent_by", "sent_by_nom",
          "sent_at", "created_at"],
         lambda d: (oid(d["_id"]), d.get("numero"), d.get("depot_order_id"), d.get("shop_id"),
                    d.get("shop_nom"), js(d.get("lines")), d.get("delivery_pdf_url"), d.get("status"),
                    js(d.get("non_conforme_items")), d.get("resolution_note"), d.get("notification_message"),
                    d.get("sent_by"), d.get("sent_by_nom"), parse_dt(d.get("sent_at")),
                    parse_dt(d.get("created_at")))),

        ("messages", "messages",
         ["id", "from_user_id", "from_user_nom", "to_user_id", "content", "attachment_url",
          "attachment_name", "created_at"],
         lambda d: (oid(d["_id"]), d.get("from_user_id"), d.get("from_user_nom"), d.get("to_user_id"),
                    d.get("content"), d.get("attachment_url"), d.get("attachment_name"),
                    parse_dt(d.get("created_at")))),

        ("help_tickets", "help_tickets",
         ["id", "subject", "description", "urgence", "created_by", "created_by_nom", "status",
          "assigned_to", "comments", "created_at"],
         lambda d: (oid(d["_id"]), d.get("subject"), d.get("description"), d.get("urgence"),
                    d.get("created_by"), d.get("created_by_nom"), d.get("status"), d.get("assigned_to"),
                    js(d.get("comments")), parse_dt(d.get("created_at")))),

        ("counters", "counters",
         ["id", "seq"],
         lambda d: (str(d["_id"]), d.get("seq", 0))),
    ]


def main():
    mongo = pymongo.MongoClient(MONGO_URL)[DB_NAME]
    sql = pymysql.connect(
        host=MARIADB_HOST, port=MARIADB_PORT, user=MARIADB_USER,
        password=MARIADB_PASSWORD, database=MARIADB_DATABASE, charset="utf8mb4",
    )
    # Ordre de synchronisation : shops et users avant les tables qui les référencent (contraintes FK).
    order = ["shops", "users", "articles", "tickets", "interventions", "devis", "reprises",
             "depot_orders", "commandes", "messages", "help_tickets", "counters"]
    specs = {s[0]: s for s in build_table_specs()}

    with sql.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS=0")
        for coll_name in order:
            _, table, columns, convert = specs[coll_name]
            docs = list(mongo[coll_name].find())
            cur.execute(f"DELETE FROM {table}")
            if docs:
                placeholders = ", ".join(["%s"] * len(columns))
                col_list = ", ".join(columns)
                rows = [convert(d) for d in docs]
                cur.executemany(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})", rows)
            print(f"  {coll_name:16s} -> {table:16s} : {len(docs)} document(s) synchronisé(s)")
        cur.execute("SET FOREIGN_KEY_CHECKS=1")
    sql.commit()
    sql.close()
    print("Synchronisation MongoDB -> MariaDB terminée.")


if __name__ == "__main__":
    main()
