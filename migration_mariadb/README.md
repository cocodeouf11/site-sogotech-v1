# Réplication MongoDB → MariaDB (sauvegarde / reporting)

## Contexte important

Le cahier des charges initial demandait une base de données relationnelle
(MariaDB/PostgreSQL). **L'environnement de développement Emergent ne fournit
que MongoDB** — c'est une contrainte de la plateforme, confirmée par le
support, pas un choix technique. L'application (backend FastAPI) est donc
développée et fonctionne sur MongoDB, y compris en production sur votre
serveur Debian 12.

Ce dossier fournit une **réplique MariaDB en lecture** de toutes les données
de l'application, pensée pour :
- la sauvegarde/consultation avec des outils SQL classiques (phpMyAdmin, DBeaver, Excel via ODBC...) ;
- le reporting/BI (requêtes SQL, jointures, tableaux croisés) ;
- l'interopérabilité avec un ERP/comptabilité qui attend du SQL.

**L'application elle-même continue de lire/écrire uniquement dans MongoDB.**
Modifier une donnée directement dans MariaDB n'aura AUCUN effet sur
l'application — cette base est une copie synchronisée à sens unique.

## Contenu

- `schema.sql` — création de la base et de toutes les tables (une table par
  collection MongoDB : shops, users, articles, tickets, interventions, devis,
  reprises, depot_orders, commandes, messages, help_tickets, counters).
  Les sous-documents à structure variable (lignes de panier, permissions,
  partages, commentaires...) sont stockés en colonnes `JSON` natives.
- `migrate_mongo_to_mariadb.py` — script de synchronisation complète
  (vide puis ré-insère chaque table à partir de MongoDB). Idempotent,
  peut être relancé autant de fois que nécessaire (ex: via cron).
- `requirements.txt` — dépendances Python du script (`pymongo`, `PyMySQL`).
- `.env.example` — variables d'environnement attendues.

Note sécurité : le hash du code PIN (`pin_hash`) n'est **jamais** copié vers
MariaDB — cette base ne doit jamais être utilisée pour l'authentification.

## Installation sur Debian 12

```bash
sudo apt install -y mariadb-server
sudo mysql_secure_installation

sudo mysql -u root -p < /opt/sogo-gestion/migration_mariadb/schema.sql

sudo mysql -u root -p -e "
CREATE USER 'sogo'@'localhost' IDENTIFIED BY '<mot_de_passe_fort>';
GRANT ALL PRIVILEGES ON sogo_gestion.* TO 'sogo'@'localhost';
FLUSH PRIVILEGES;"
```

## Exécuter la synchronisation

```bash
cd /opt/sogo-gestion/migration_mariadb
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # puis renseigner MONGO_URL, MARIADB_PASSWORD, etc.
set -a && source .env && set +a
python3 migrate_mongo_to_mariadb.py
```

## Automatiser (cron, ex: toutes les nuits à 2h)

```bash
crontab -e
# ajouter :
0 2 * * * cd /opt/sogo-gestion/migration_mariadb && source venv/bin/activate && set -a && source .env && set +a && python3 migrate_mongo_to_mariadb.py >> /var/log/sogo-sync-mariadb.log 2>&1
```

## Vérifié dans cette session

Le schéma et le script ont été testés de bout en bout (installation MariaDB,
création du schéma, synchronisation des données réelles de l'application :
articles, tickets, interventions, devis, reprises, commandes, etc.) — voir
`/app/memory/PRD.md` pour le détail.
