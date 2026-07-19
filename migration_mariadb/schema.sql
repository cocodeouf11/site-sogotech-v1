-- ============================================================================
-- Schéma MariaDB pour SOGO Gestion (Boutique / Dépôt)
-- ============================================================================
-- Ce schéma reproduit fidèlement les collections MongoDB de l'application
-- sous forme de tables relationnelles. Les champs qui contiennent des
-- sous-documents à structure variable (lignes de panier, permissions,
-- partages, etc.) sont stockés en colonnes JSON — c'est l'approche standard
-- pour répliquer un modèle "document" vers une base relationnelle sans
-- exploser le nombre de tables ni perdre d'information.
--
-- IMPORTANT : ce schéma est destiné à un usage de SAUVEGARDE / REPORTING /
-- INTEROPÉRABILITÉ (ex: connecter un outil BI, exporter vers un ERP, etc.).
-- L'application (backend FastAPI) continue de fonctionner sur MongoDB —
-- voir /app/migration_mariadb/README.md pour le contexte complet.
--
-- Compatible MariaDB 10.5+ (Debian 12 fournit MariaDB 10.11 par défaut).
-- ============================================================================

CREATE DATABASE IF NOT EXISTS sogo_gestion CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sogo_gestion;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shops (
    id            VARCHAR(24) PRIMARY KEY,
    nom           VARCHAR(255) NOT NULL,
    type          VARCHAR(20)  NOT NULL,   -- 'boutique' ou 'depot'
    adresse       VARCHAR(500),
    telephone     VARCHAR(50),
    siret         VARCHAR(50),
    logo_url      VARCHAR(500),
    created_at    DATETIME,
    synced_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- Note sécurité : le hash du code PIN (pin_hash) n'est PAS répliqué ici.
-- Cette base ne doit jamais servir à l'authentification.
CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(24) PRIMARY KEY,
    nom             VARCHAR(100),
    prenom          VARCHAR(100),
    poste           VARCHAR(100),
    grades          JSON,
    shop_id         VARCHAR(24),
    active_shop_id  VARCHAR(24),
    telephone       VARCHAR(50),
    is_admin        BOOLEAN DEFAULT FALSE,
    active          BOOLEAN DEFAULT TRUE,
    permissions     JSON,
    created_at      DATETIME,
    synced_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_shop FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS articles (
    id            VARCHAR(24) PRIMARY KEY,
    code          VARCHAR(50),
    nom           VARCHAR(255),
    quantite      INT DEFAULT 0,
    categorie     VARCHAR(100),
    prix          DECIMAL(10,2) DEFAULT 0,
    photo_url     VARCHAR(500),
    shop_id       VARCHAR(24),
    created_at    DATETIME,
    synced_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_articles_shop FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL,
    INDEX idx_articles_shop (shop_id),
    INDEX idx_articles_code (code)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tickets (
    id            VARCHAR(24) PRIMARY KEY,
    type          VARCHAR(20),          -- 'ticket' ou 'facture'
    numero        VARCHAR(50),
    shop_id       VARCHAR(24),
    vendeur_id    VARCHAR(24),
    vendeur_nom   VARCHAR(200),
    doc_date      VARCHAR(20),          -- date affichée (format JJ/MM/AAAA)
    items         JSON,
    tva_percent   DECIMAL(5,2),
    total_ht      DECIMAL(12,2),
    total_tva     DECIMAL(12,2),
    total_ttc     DECIMAL(12,2),
    client_info   JSON,
    shared_with   JSON,
    created_at    DATETIME,
    synced_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_tickets_shop FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL,
    INDEX idx_tickets_shop (shop_id),
    INDEX idx_tickets_numero (numero)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS interventions (
    id                       VARCHAR(24) PRIMARY KEY,
    numero                   VARCHAR(50),
    shop_id                  VARCHAR(24),
    client_nom               VARCHAR(200),
    client_tel               VARCHAR(50),
    client_email             VARCHAR(200),
    client_adresse           VARCHAR(500),
    materiel                 VARCHAR(255),
    imei                     VARCHAR(50),
    motif                    TEXT,
    intervention_effectuee   TEXT,
    signature_data           LONGTEXT,
    vendeur_id               VARCHAR(24),
    vendeur_nom              VARCHAR(200),
    doc_date                 VARCHAR(20),
    shared_with              JSON,
    created_at               DATETIME,
    synced_at                DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_interventions_shop FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL,
    INDEX idx_interventions_shop (shop_id),
    INDEX idx_interventions_numero (numero)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS devis (
    id                VARCHAR(24) PRIMARY KEY,
    numero            VARCHAR(50),
    shop_id           VARCHAR(24),
    client_nom        VARCHAR(200),
    client_tel        VARCHAR(50),
    client_email      VARCHAR(200),
    items             JSON,
    intervention_ids  JSON,
    mentions_legales  TEXT,
    signature_data    LONGTEXT,
    vendeur_id        VARCHAR(24),
    vendeur_nom       VARCHAR(200),
    doc_date          VARCHAR(20),
    status            VARCHAR(30),
    shared_with       JSON,
    created_at        DATETIME,
    synced_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_devis_shop FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL,
    INDEX idx_devis_shop (shop_id),
    INDEX idx_devis_numero (numero)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reprises (
    id                  VARCHAR(24) PRIMARY KEY,
    numero              VARCHAR(50),
    shop_id             VARCHAR(24),
    client_nom          VARCHAR(200),
    client_tel          VARCHAR(50),
    client_email        VARCHAR(200),
    client_adresse      VARCHAR(500),
    modele              VARCHAR(200),
    capacite            VARCHAR(50),
    imei                VARCHAR(50),
    etat_produit        JSON,
    tests               JSON,
    batterie_pourcentage INT,
    remarques           TEXT,
    defauts_marks       JSON,
    piece_a_remplacer   VARCHAR(255),
    offre_rachat        DECIMAL(10,2),
    bon_pour_accord     BOOLEAN DEFAULT FALSE,
    signature_data      LONGTEXT,
    vendeur_id          VARCHAR(24),
    vendeur_nom         VARCHAR(200),
    doc_date            VARCHAR(20),
    shared_with         JSON,
    created_at          DATETIME,
    synced_at           DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_reprises_shop FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL,
    INDEX idx_reprises_shop (shop_id),
    INDEX idx_reprises_numero (numero)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS depot_orders (
    id                VARCHAR(24) PRIMARY KEY,
    numero            VARCHAR(50),
    delivery_pdf_url  VARCHAR(500),
    label_pdf_url     VARCHAR(500),
    `lines`           JSON,
    status            VARCHAR(30),
    created_by        VARCHAR(24),
    created_at        DATETIME,
    synced_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_depot_orders_numero (numero)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS commandes (
    id                    VARCHAR(24) PRIMARY KEY,
    numero                VARCHAR(50),
    depot_order_id        VARCHAR(24),
    shop_id               VARCHAR(24),
    shop_nom              VARCHAR(255),
    `lines`               JSON,
    delivery_pdf_url      VARCHAR(500),
    status                VARCHAR(30),
    non_conforme_items    JSON,
    resolution_note       TEXT,
    notification_message  TEXT,
    sent_by               VARCHAR(24),
    sent_by_nom           VARCHAR(200),
    sent_at               DATETIME,
    created_at            DATETIME,
    synced_at             DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_commandes_shop FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL,
    INDEX idx_commandes_shop (shop_id),
    INDEX idx_commandes_numero (numero)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id                VARCHAR(24) PRIMARY KEY,
    from_user_id      VARCHAR(24),
    from_user_nom     VARCHAR(200),
    to_user_id        VARCHAR(24),
    content           TEXT,
    attachment_url    VARCHAR(500),
    attachment_name   VARCHAR(255),
    created_at        DATETIME,
    synced_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_messages_from (from_user_id),
    INDEX idx_messages_to (to_user_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS help_tickets (
    id                VARCHAR(24) PRIMARY KEY,
    subject           VARCHAR(255),
    description       TEXT,
    urgence           VARCHAR(20),
    created_by        VARCHAR(24),
    created_by_nom    VARCHAR(200),
    status            VARCHAR(30),
    assigned_to       VARCHAR(24),
    comments          JSON,
    created_at        DATETIME,
    synced_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- Compteurs de numérotation auto (ART-, INT-YYYY-, DEV-YYYY-, etc.)
CREATE TABLE IF NOT EXISTS counters (
    id    VARCHAR(50) PRIMARY KEY,
    seq   INT DEFAULT 0
) ENGINE=InnoDB;
