# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Deux briques complémentaires autour d'une plateforme de questions/réponses sur un corpus documentaire (GT « Harmonisation CBS », DGPR) :

1. **Synchronisation Python** (`src/`) : récupère l'arborescence d'un document de la Suite Numérique – Docs (`docs.numerique.gouv.fr`) et l'envoie dans la table Grist `Chapitres`.
2. **Widgets Grist** (`grist_widgets/`) : widgets HTML/JS (parcours-doc, echanges, questions) qui exploitent ces chapitres dans le document Grist.

Le code, les commentaires et les messages sont en français.

## Commandes

```powershell
python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt
python src/sync.py 'https://docs.numerique.gouv.fr/docs/<uuid>/'   # ou l'UUID seul
```

Il n'y a ni tests automatisés, ni linter, ni build. Le débogage pas-à-pas se fait dans `notebooks/test_sync.ipynb` (cellules à exécuter dans l'ordre ; la cellule 5 envoie un seul record, la 8 envoie tout).

Configuration dans `.env` (voir le README pour la liste). L'authentification Docs repose sur les cookies navigateur `docs_sessionid` / `csrftoken` (session ProConnect) : ils expirent, et une erreur 401/403 sur l'API Docs signifie en général qu'il faut les renouveler.

## Architecture de la synchronisation

`sync.py` enchaîne : `DocsClient.get_tree()` → `flatten_tree()` → `sanitize_for_waf()` → `GristClient.send_records()`.

- **`flatten_tree()`** (`src/docs_client.py`) parcourt l'arbre récursivement et produit un record `{"fields": {...}}` par nœud (titre, emoji, niveau, `ordre` décodé depuis le `path` base-36 de Docs, `numero` hiérarchique type `1.3.2`, url, contenu).
- **Format du contenu** : `CONTENT_FORMAT = "json"` dans `sync.py`. Le JSON BlockNote est converti en Markdown par `blocknote_to_markdown()` / `_render_block()` / `_render_inline()`, qui est le seul chemin qui préserve callouts, tableaux fusionnés et émojis. Les modes `markdown` / `html` / `auto` (via le Y-Provider) sont dégradés et gardés pour comparaison. Les mentions vers d'autres docs ne sont pas résolubles via l'API : elles deviennent `[référence interne]`.
- **Images internes** Docs (nécessitent une session) : `embed_internal_images()` les pousse dans le dépôt GitHub (`images/`, dédoublonnage par UUID, d'où les commits automatiques « chore: add Docs attachment … ») si `GITHUB_TOKEN` est défini, sinon les embarque en data URI base64.
- **`sanitize_for_waf()`** retire les blocs de code SQL du contenu : le WAF devant Grist rejette les requêtes qui en contiennent.
- **`GristClient`** : seules les colonnes de `GRIST_COLUMNS` sont envoyées ; `contenu` est tronqué à 100 000 caractères. L'envoi se fait **un record à la fois avec 3 s de pause** (`add_records`), et c'est toujours un ajout (`AddRecord`), jamais une mise à jour : relancer la sync crée des doublons dans `Chapitres`.

## Widgets Grist

- `grist_widgets/grist_code.py` est l'export du schéma du document Grist (tables `Chapitres`, `Questions`, `Reponses`, `Reponse_Chapitre_Link`, `Votes`, `Users`, `Widget_Session`, etc.). C'est la référence pour les noms de tables/colonnes utilisés par les widgets via `grist.docApi.fetchTable` / `applyUserActions`.
- Pas de npm ni de bundler : chaque widget est un `index.html` + `widget.js` autonomes, dépendances uniquement via CDN ; `grist-plugin-api.js` est chargé depuis `https://docs.getgrist.com/grist-plugin-api.js`.
- Toujours appeler `grist.ready()` avant tout appel à l'API Grist (sinon `RPC_UNKNOWN_FORWARD_DEST`).
- Déploiement, deux modes (testé avec succès le 2026-09-23 sur l'instance Grist utilisée par le GT) :
  - **par URL (GitHub Pages)** : `https://nantodevison.github.io/docs-suite-numerique/grist_widgets/<widget>/`. Grist affiche un avertissement « source inconnue » à confirmer, puis il faut régler le niveau d'accès du widget sur « Accès complet ». Dans ce mode, l'arborescence du dépôt fait partie de l'URL : **déplacer un dossier de widget casse les widgets branchés dessus** ;
  - **par copier-coller** dans l'éditeur de Custom Widget (onglet HTML : `index.html`, onglet JavaScript : `widget.js`).
- Chaque `index.html` charge `widget.js` par `<script src="widget.js">` : indispensable en mode URL, sans effet en copier-coller.
- Les URL raw GitHub (`raw.githubusercontent.com`) ne conviennent pas aux widgets (le HTML y est servi comme du texte brut) ; elles restent valables pour les images.
- Le widget `echanges` envoie des emails via l'API Brevo ; c'est désactivé par `var NOTIFICATIONS_ENABLED = false;` en tête de `grist_widgets/echanges/widget.js` (fonctions `notifyOnNewResponse`, `sendSollicitation`, `notifyAuthor`).
