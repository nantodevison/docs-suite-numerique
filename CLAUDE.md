# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Boîte à outils du groupe PMD (Politique de Mobilité Durable, Cerema Sud-Ouest) autour de la **Suite Numérique** (Docs, Grist, Fichiers). But : capitaliser des fonctionnalités de type Notion (Kanban, fiches, parcours documentaires…) sous forme de widgets Grist réutilisables, pour les diffuser auprès des collègues.

Le code, les commentaires et les messages sont en français. Le dépôt est **public** : jamais de données (contacts, retours, écoutes client…) ni de secrets ; ceux-ci vont dans `.env` (non versionné).

## Organisation

| Dossier | Contenu |
|---|---|
| `widgets/` | Tous les widgets Grist, **à plat** (un dossier par widget), et leur catalogue dans `widgets/README.md` |
| `python/` | Synchronisation Docs → Grist (`docs_client.py`, `grist_client.py`, `sync.py`, notebook `test_sync.ipynb`) |
| `espaces/<document>/` | Schéma de chaque document Grist (`grist_schema.py`, export du code Grist, sans données) : référence pour les noms de tables et de colonnes |
| `projets/<projet>/` | Ce qui est propre à un projet, hors widgets : README (besoin, widgets utilisés), modèles Docs, archives |
| `images/` | Images publiées par la synchronisation (URL déjà utilisées dans Grist : ne pas déplacer) |

Le document Grist principal est `espaces/gestion-projets/` : un espace unique (gestion de projet, CRM, retours utilisateurs, valorisation, écoute client) organisé autour de la table `Projets2`. Les projets (Valorisation, Écoute client, Observatoire des trafics…) sont des **lignes** de `Projets2`, pas des documents séparés.

## Widgets Grist

- Pas de npm ni de bundler : chaque widget est un `index.html` + un fichier JS autonomes, dépendances uniquement via CDN ; `grist-plugin-api.js` est chargé depuis `https://docs.getgrist.com/grist-plugin-api.js`.
- Toujours appeler `grist.ready()` avant tout appel à l'API Grist (sinon `RPC_UNKNOWN_FORWARD_DEST`).
- Déploiement, deux modes (par URL testé avec succès le 2026-09-23 sur l'instance Grist de la DINUM) :
  - **par URL (GitHub Pages, branche `master`)** : `https://nantodevison.github.io/pmd-suite-numerique/widgets/<widget>/`. Grist affiche un avertissement « source inconnue » à confirmer, puis il faut régler le niveau d'accès du widget sur « Accès complet » ;
  - **par copier-coller** dans l'éditeur de Custom Widget (onglet HTML : `index.html`, onglet JavaScript : le fichier JS).
- `index.html` charge le fichier JS par `<script src="…">` : indispensable en mode URL, sans effet en copier-coller.
- **Ne jamais déplacer ni renommer le dossier d'un widget publié** : le chemin fait partie de l'URL, et les documents Grist qui l'utilisent casseraient. Un widget ne se range pas par projet ni par généricité : ce classement va dans le catalogue.
- Les dossiers `widgets/_…` (gabarit, code JS partagé) ne sont pas des widgets ; ils sont publiés grâce à `.nojekyll` à la racine.
- Pour rendre un widget réutilisable, privilégier l'association de colonnes (configurée par l'utilisateur) et le filtrage natif de Grist (« Sélectionner par ») plutôt que des noms de tables ou de colonnes codés en dur.
- Les URL raw GitHub (`raw.githubusercontent.com`) ne conviennent pas aux widgets (le HTML y est servi comme du texte brut) ; elles restent valables pour les images.

### Catalogue des widgets

Tout ajout de widget, et tout changement de portée, de projet ou de statut, se reporte dans le catalogue `widgets/README.md`, selon le format défini en tête de ce fichier. Claude remplit les champs lisibles dans le code (Données, Accès), propose le Rôle, et **demande toujours** la Portée, le(s) Projet(s) et le Statut à l'utilisateur, sauf s'il vient de les indiquer explicitement.

## Synchronisation Docs → Grist (`python/`)

```powershell
python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt
python python/sync.py 'https://docs.numerique.gouv.fr/docs/<uuid>/'   # ou l'UUID seul
```

Il n'y a ni tests automatisés, ni linter, ni build. Le débogage pas-à-pas se fait dans `python/test_sync.ipynb` (cellules à exécuter dans l'ordre ; la cellule 5 envoie un seul record, la 8 envoie tout).

Configuration dans `.env` à la racine (voir `python/README.md` pour la liste). L'authentification Docs repose sur les cookies navigateur `docs_sessionid` / `csrftoken` (session ProConnect) : ils expirent, et une erreur 401/403 sur l'API Docs signifie en général qu'il faut les renouveler.

`sync.py` enchaîne : `DocsClient.get_tree()` → `flatten_tree()` → `sanitize_for_waf()` → `GristClient.send_records()`.

- **`flatten_tree()`** (`python/docs_client.py`) parcourt l'arbre récursivement et produit un record `{"fields": {...}}` par nœud (titre, emoji, niveau, `ordre` décodé depuis le `path` base-36 de Docs, `numero` hiérarchique type `1.3.2`, url, contenu).
- **Format du contenu** : `CONTENT_FORMAT = "json"` dans `sync.py`. Le JSON BlockNote est converti en Markdown par `blocknote_to_markdown()` / `_render_block()` / `_render_inline()`, qui est le seul chemin qui préserve callouts, tableaux fusionnés et émojis. Les modes `markdown` / `html` / `auto` (via le Y-Provider) sont dégradés et gardés pour comparaison. Les mentions vers d'autres docs ne sont pas résolubles via l'API : elles deviennent `[référence interne]`.
- **Images internes** Docs (nécessitent une session) : `embed_internal_images()` les pousse dans le dépôt GitHub (`images/`, dédoublonnage par UUID, d'où les commits automatiques « chore: add Docs attachment … ») si `GITHUB_TOKEN` est défini, sinon les embarque en data URI base64. Le dépôt étant public, utiliser base64 pour tout contenu sensible.
- **`sanitize_for_waf()`** retire les blocs de code SQL du contenu : le WAF devant Grist rejette les requêtes qui en contiennent.
- **`GristClient`** : seules les colonnes de `GRIST_COLUMNS` sont envoyées ; `contenu` est tronqué à 100 000 caractères. L'envoi se fait **un record à la fois avec 3 s de pause** (`add_records`), et c'est toujours un ajout (`AddRecord`), jamais une mise à jour : relancer la sync crée des doublons dans `Chapitres`.
- La sync est aujourd'hui câblée pour le GT CBS (table `Chapitres`, schéma dans `espaces/gt-cbs-bruit/grist_schema.py`).

## GT CBS (projet terminé)

Les widgets `parcours-doc`, `questions` et `echanges` (statut « archivé ») servaient la plateforme de questions/réponses du GT « Harmonisation CBS » (DGPR). Le widget `echanges` envoie des emails via l'API Brevo ; c'est désactivé par `var NOTIFICATIONS_ENABLED = false;` en tête de `widgets/echanges/widget.js` (fonctions `notifyOnNewResponse`, `sendSollicitation`, `notifyAuthor`).
