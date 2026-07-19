# Déploiement sur Debian 12

Cette application utilise React (frontend), FastAPI (backend) et MongoDB. Ce guide couvre l'installation manuelle sur un serveur Debian 12 avec Nginx en reverse proxy et systemd pour la gestion des services.

> Note technique : le cahier des charges demandait une base de données relationnelle (PostgreSQL/MariaDB). L'environnement de développement Emergent impose MongoDB. L'application a donc été livrée avec MongoDB (via Motor, driver async). MongoDB dispose d'un dépôt APT officiel pour Debian 12 et s'installe aussi nativement en quelques commandes (voir ci-dessous). Si une base strictement relationnelle est requise en production, une migration vers PostgreSQL est possible ultérieurement (les modèles Pydantic facilitent la ré-écriture de la couche base de données).

## 1. Dépendances système

```bash
sudo apt update && sudo apt install -y \
  python3.11 python3.11-venv python3-pip \
  nginx curl gnupg build-essential

# Node.js LTS (20.x)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g yarn

# MongoDB (dépôt officiel MongoDB pour Debian 12)
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update && sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
```

## 2. Récupération du code et configuration

```bash
sudo mkdir -p /opt/sogo-gestion && cd /opt/sogo-gestion
# copier le contenu de backend/ et frontend/ ici

cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

Créer `/opt/sogo-gestion/backend/.env` :
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="sogo_gestion"
CORS_ORIGINS="https://votre-domaine.fr"
JWT_SECRET="<générer avec: openssl rand -hex 32>"
ADMIN_PIN="<pin admin initial 6 chiffres>"
UPLOAD_DIR="uploads"
```

Build du frontend :
```bash
cd /opt/sogo-gestion/frontend
echo 'REACT_APP_BACKEND_URL=https://votre-domaine.fr' > .env
yarn install
yarn build
```

## 3. Service systemd (backend)

`/etc/systemd/system/sogo-backend.service` :
```ini
[Unit]
Description=SOGO Gestion Backend (FastAPI)
After=network.target mongod.service

[Service]
User=www-data
WorkingDirectory=/opt/sogo-gestion/backend
Environment="PATH=/opt/sogo-gestion/backend/venv/bin"
ExecStart=/opt/sogo-gestion/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sogo-backend
```

## 4. Nginx (reverse proxy + fichiers statiques)

`/etc/nginx/sites-available/sogo-gestion` :
```nginx
server {
    listen 80;
    server_name votre-domaine.fr;

    root /opt/sogo-gestion/frontend/build;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8001;
    }

    location / {
        try_files $uri /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/sogo-gestion /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Ajouter HTTPS avec certbot (`sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx -d votre-domaine.fr`).

## 5. Sauvegardes

```bash
mongodump --db sogo_gestion --out /var/backups/sogo-gestion/$(date +%F)
```
Planifier via cron quotidien.

## 6. Réplication MariaDB (reporting / sauvegarde secondaire)

Un outil complet de réplication MongoDB → MariaDB est fourni dans
`/opt/sogo-gestion/migration_mariadb/` (schéma SQL + script de
synchronisation testé). Il permet de consulter/exporter toutes les données
de l'application via SQL classique, sans changer le fonctionnement de
l'application (qui reste sur MongoDB). Voir
`migration_mariadb/README.md` pour la procédure complète d'installation et
d'automatisation (cron).
