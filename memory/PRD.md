# PRD — Application de gestion Boutique/Dépôt

## Problème d'origine
Application web de gestion pour entreprise avec deux modules : **Boutique** et **Dépôt**. Auth par code PIN, permissions granulaires par grade/utilisateur, cloisonnement des données par boutique, documents PDF A4 avec signature tactile (Intervention, Devis, Reprise), Caisse avec tickets/factures, module Dépôt reprenant les fonctionnalités de picking d'entrepôt du repo `site-sogo-v2`. Cible de déploiement : Debian 12 (voir `/app/DEPLOYMENT.md`).

## Choix utilisateur (recueillis via ask_human)
- Base de données : MariaDB demandée → **déviation documentée** : l'environnement de développement Emergent n'expose que MongoDB (Motor). Voir note dans DEPLOYMENT.md.
- Auth : PIN 6 chiffres + JWT (cookie httpOnly), pas d'OAuth.
- Dépôt : fonctionnalités du repo de référence répliquées dans la stack React/FastAPI (pas d'import direct du code), fonction "reprise" du dépôt exclue (doublon avec la fiche de reprise Boutique).
- Logo : placeholder généré, modifiable dans Admin > Boutiques.
- Signature : canvas HTML5 custom (pas de lib tierce).

## Architecture
- **Backend** : FastAPI, MongoDB (motor), JWT cookie auth, reportlab (PDF A4 + ticket), PyMuPDF (parsing texte bons de livraison).
- **Frontend** : React 19, React Router 7, Tailwind + shadcn/ui, signature pad canvas custom, thème clair/sombre (next-themes pattern via ThemeContext).
- Fichiers backend : `server.py`, `database.py`, `auth_utils.py`, `constants.py` (grades/permissions), `pdf_utils.py`, `routers/*` (auth, users, shops, stock, caisse, intervention, devis, reprise, communication, depot).
- Uploads (photos articles, logos, signatures encodées base64 dans les documents, pièces jointes messagerie, PDF dépôt) stockés sur disque local `/app/backend/uploads`, servis via StaticFiles — choix cohérent avec la cible auto-hébergée Debian 12 (pas d'object storage cloud).

## Personas
- **Admin** : accès total, gère utilisateurs/grades/permissions/boutiques/logos.
- **Gestionnaire toutes boutiques** : voit et ouvre tous les documents de toutes les boutiques.
- **Gestionnaire/Responsable de boutique, Technicien, Vendeur** : accès selon permissions et boutique d'affectation.
- **Chef de dépôt / Magasinier** : module Dépôt (picking), Intervention/Devis (pas Reprise Boutique).

## Ce qui est implémenté (17 juillet 2026)
- Auth PIN + JWT cookie, seed admin (PIN 123456), seed boutique + dépôt par défaut.
- Gestion utilisateurs : CRUD, grades multiples, permissions granulaires par module (reprise/devis/caisse/intervention/stock/communication), templates de permissions par grade avec surcharge admin.
- Gestion boutiques/dépôts : CRUD + upload logo.
- Stock : CRUD articles + photo, vue grille de cartes carrées.
- Caisse : ticket/facture, articles + prestations libres, TVA modifiable, calcul HT/TVA/TTC, PDF (A4 facture / ticket format réduit), décrément stock automatique.
- Intervention : fiche A4 complète, numérotation auto (INT-YYYY-NNNN, modifiable), signature tactile, export PDF.
- Devis : lignes d'articles/prestations, rattachement fiches d'intervention, mentions légales modifiables, signature, export PDF.
- Reprise téléphone : cases état produit + tests, schéma cliquable avant/arrière (marques défauts), remarques, pièce à remplacer, offre de rachat, texte légal obligatoire, case "bon pour accord", signature, export PDF.
- Cloisonnement des données : listes visibles par tous, détail restreint (403) sauf Admin/Gestionnaire toutes boutiques — implémenté pour intervention/devis/reprise.
- Communication : messagerie 1-à-1 avec pièces jointes, tickets d'aide avec urgence (basse/moyenne/haute/critique) + commentaires + statuts.
- Dépôt : upload bon de livraison PDF avec parsing heuristique des lignes (regex), ajout manuel de ligne, validation tactile ligne par ligne (+/-/reset), étiquette Chronopost (affichage simple, sans recadrage auto), statut auto (en_attente/en_cours/terminé).
- Thème clair/sombre avec persistance localStorage.
- `DEPLOYMENT.md` : guide Debian 12 (apt, systemd, Nginx reverse proxy, certbot, sauvegardes mongodump).

## Tests effectués
- Backend : 28/28 tests pytest (auth, permissions, CRUD tous modules, cloisonnement 403, PDF content-type, dépôt picking).
- Frontend : parcours complet testés (login PIN, stock, caisse, intervention, devis, reprise avec signature/diagramme, admin, dépôt, thème). Bug corrigé : `batterie_pourcentage`/`offre_rachat` mal formatés en 422 lors de la création de reprise (RepriseFormPage.jsx) — corrigé et revérifié.

## Backlog priorisé (P0/P1/P2)
- **P0** : Aucun bloquant restant après correctifs.
- **P1** :
  - Recadrage automatique des étiquettes Chronopost (actuellement affichage brut du PDF, pas de crop image comme le repo de référence).
  - Amélioration du parsing PDF de bons de livraison (actuellement heuristique regex simple ligne "nom + quantité"; le repo de référence utilise une détection de bbox plus robuste).
  - Rafraîchissement JWT (actuellement token unique 12h sans refresh token).
- **P2** :
  - Export PDF multi-pages avec pagination visuelle plus fine pour devis/factures longues.
  - Recherche/filtre sur les listes (interventions, devis, reprises, stock).
  - Historique/audit des modifications de permissions.

## Prochaines actions suggérées
- Migrer vers PostgreSQL/MariaDB si un hébergement strictement relationnel est requis en production (les routers sont isolés par module, migration ciblée possible).
- Ajouter la recherche et le filtre sur les listes de documents pour les grandes boutiques.
- Envisager la notification (email/SMS) sur nouveaux tickets d'aide critiques.
