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

## Itération 2 (17 juillet 2026) — Dépôt : picking réel + outil Étiquette
- Reparsing des bons de livraison PDF calibré sur le format réel fourni par l'utilisateur : extraction description produit + UGS/Étagère/Colonne/Tiroir/Bac, N° de commande auto-extrait ("N° de commande :" + ligne suivante), fallback CMD-{timestamp} si non trouvé. Testé et validé sur un vrai bon de livraison 180 lignes / 285 unités / commande 56747 — extraction 100% exacte.
- Commande dépôt : suppression du champ numéro manuel (auto-extrait), affichage "CMD {numero}" + "{picked}/{total} · {percent}%" avec barre de progression, correspondant exactement au rendu de référence fourni par l'utilisateur.
- Pastille "tap-to-pick" : bouton rond "{picked}/{quantité}" cliqué autant de fois que la quantité (nouvel endpoint POST /depot/orders/{id}/lines/{line_id}/tap qui incrémente de 1, ou repasse à 0 si déjà au maximum). Statut auto (en_attente/en_cours/terminé).
- Page détail commande : en-tête avec retour, titre, progression, menu "ACTIONS" (bon de livraison, étiquette, suppression).
- Nouvel outil **Étiquette** (`/depot/etiquette`) répliquant fidèlement l'outil HTML fourni par l'utilisateur : upload PDF/JPG/PNG, rendu page 1 via pdf.js (CDN, cadrage fixe calibré x0=0.6067,y0=0.1525,x1=0.9812,y1=0.8439, échelle 2.2), aperçu découpé, boutons Imprimer / Télécharger PNG / Télécharger PDF (jsPDF CDN). 100% côté client, aucune dépendance backend.
- Tests : 35/35 backend (28 précédents + 7 nouveaux dépôt), frontend Dépôt + Étiquette validés bout en bout, aucun bug résiduel.

## Itération 3 (17 juillet 2026) — SIRET, recherche, permissions ticket/intervention
- SIRET boutique : nouveau champ dans Admin > Boutiques, affiché sur l'en-tête de tous les documents (écran + PDF).
- Caisse : recherche articles + affichage en liste (au lieu de grille), recherche historique, nom du créateur affiché sur ticket/facture, actions Voir/Modifier/Supprimer par ligne (permission caisse.delete_ticket + créateur), champ SIRET client sur facture.
- Stock : barre de recherche, champ "ID article" (auto-généré ART-NNNN si vide, sinon valeur saisie avec contrôle d'unicité).
- Intervention/Devis/Reprise : barre de recherche sur les listes, lien "Modifier"/"Voir" selon permission, bouton Supprimer gaté par permission.
- Correctif défensif : blocage de la création si l'utilisateur n'a pas de boutique valide assignée (au lieu d'un fallback silencieux vers une autre boutique).
- Tests : 43/43 backend, vérification bout en bout du signalement "même boutique ne peut pas visualiser" — confirmé fonctionnel (utilisateurs de la même boutique voient et ouvrent bien les documents des collègues).

## Itération 4 (18 juillet 2026) — Responsive mobile/tablette
- Sidebar transformée en tiroir (drawer) sur mobile/tablette (<1024px) avec bouton hamburger, overlay, bouton fermeture, fermeture auto à la navigation ; reste statique sur desktop.
- Correctif critique (signalé par capture d'écran) : pastille de picking Dépôt qui recouvrait le texte du produit sur mobile — désormais empilée sous le texte (colonne sur mobile, ligne dès `sm:`).
- Toutes les listes (Intervention/Devis/Reprise/Utilisateurs) défilables horizontalement sur mobile au lieu d'écraser les colonnes ; barres de recherche + boutons empilés verticalement sur petit écran.
- Formulaires A4 (Intervention/Devis/Reprise) et en-tête de document en une colonne sur mobile, padding réduit, aucun débordement horizontal.
- Caisse : lignes d'historique réorganisées pour ne plus se chevaucher sur petit écran.
- Tests : 100% (9/9) validés par l'agent de test sur mobile (390px), tablette (768px) et desktop (1920px), aucune régression détectée.

## Itération 5 (19 juillet 2026) — Permission Dépôt + workflow Commande
- Nouvelle permission booléenne "Dépôt" : masque le lien Dépôt et bloque les routes/API (403) si non attribuée. Migration automatique au démarrage pour les utilisateurs existants selon leur grade.
- Nouvel onglet "Commande" (visible par tous) : le Dépôt envoie un bon de livraison à une boutique via ACTIONS > "Envoyer à une boutique" ; la boutique destinataire valide ("Tout est conforme" → ajout automatique au stock, articles existants incrémentés par nom, nouveaux créés avec code UGS ou auto-généré) ou signale une non-conformité (sélection des articles + description).
- Cloisonnement : chaque boutique ne voit que ses propres commandes ; les utilisateurs avec permission Dépôt (ou admin) voient tout.
- Notification automatique après résolution, visible uniquement par les détenteurs de la permission Dépôt (bannière en haut de l'onglet Commande, champ absent de l'API pour les autres).
- Tests : 16/16 backend, scénario complet à 2 boutiques validé en UI (isolation confirmée), aucun bug trouvé.

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
  - Refresh token JWT (actuellement token unique 12h sans refresh token).
- **P2** :
  - Export PDF multi-pages avec pagination visuelle plus fine pour devis/factures longues.
  - Recherche/filtre sur les listes (interventions, devis, reprises, stock).
  - Historique/audit des modifications de permissions.

## Prochaines actions suggérées
- Migrer vers PostgreSQL/MariaDB si un hébergement strictement relationnel est requis en production (les routers sont isolés par module, migration ciblée possible).
- Ajouter la recherche et le filtre sur les listes de documents pour les grandes boutiques.
- Envisager la notification (email/SMS) sur nouveaux tickets d'aide critiques.
