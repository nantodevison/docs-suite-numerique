# docs-suite-numerique

Synchronisation des documents de la **Suite Numérique – Docs** vers **Grist**.

## Structure du projet

```
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── docs_client.py   # Client API Docs (récupération, conversion, images)
│   ├── grist_client.py  # Client API Grist (envoi des records)
│   └── sync.py          # Script principal de synchronisation
├── notebooks/
│   └── test_sync.ipynb  # Notebook de test et debug pas-à-pas
└── grist_widgets/       # Widgets Grist (HTML/CSS/JS)
    ├── README.md        # Organisation et workflow
    ├── parcours-doc/    # Widget 1 – Navigation chapitres
    ├── echanges/        # Widget 2 – Fil de discussion / échanges
    └── questions/       # Widget 3 – Questions / Réponses
```

---

## Fonctionnement général

Le script récupère l'arborescence d'un document Docs (via l'API Docs), aplatit
chaque nœud en un record Grist, et envoie le tout dans la table `Chapitres`.

### Pipeline de synchronisation

```
Docs (API) → get_tree()
           → flatten_tree()     ← format JSON BlockNote (recommandé)
           → blocknote_to_markdown()
           → embed_internal_images()   ← GitHub ou base64
           → sanitize_for_waf()        ← suppression blocs SQL (contenu uniquement)
           → send_records()     → Grist
```

### Champs produits par `flatten_tree()`

| Champ | Description |
|---|---|
| `titre` | Titre complet avec émoji (ex : `🌟 Guide`) |
| `emoji` | Émoji extrait du titre (ex : `🌟`) |
| `titre_propre` | Titre sans émoji (ex : `Guide`) |
| `niveau` | Profondeur dans l'arbre (1 = premier niveau) |
| `ordre` | Ordre natif Docs (base-36 → entier) |
| `numero` | Numérotation hiérarchique (ex : `1.3.2`) |
| `url` | URL du document Docs |
| `contenu` | Contenu converti en markdown |
| `contenu_format` | Format utilisé (`json→md`, `html`, `markdown`, `erreur`) |

### Formats de récupération du contenu (`content_format`)

| Valeur | Comportement | Émojis corps | Callouts | Tableaux | `[référence interne]` |
|---|---|---|---|---|---|
| `json` (**recommandé**) | JSON BlockNote → markdown via `blocknote_to_markdown()` | ✓ | ✓ | ✓ (avec fusions) | ✓ explicite |
| `markdown` | Markdown brut depuis le Y-Provider | ⚠️ partiel | ❌ perdus | ⚠️ basique | ❌ silencieux |
| `html` | HTML → texte via `html_to_text()` | ✓ | ⚠️ approx. | ⚠️ basique | ❌ silencieux |
| `auto` | Essaie `markdown`, bascule sur `html` si Y-Provider plante | ✓ | ❌ | ⚠️ | ❌ silencieux |

> Le format `json` est celui utilisé par défaut dans `sync.py` et dans le notebook.
> Les références internes Docs (`@mention` vers d'autres documents) ne peuvent pas
> être résolues via l'API — elles sont marquées `[référence interne]` en mode `json`.

### Gestion des images internes

Les images uploadées dans Docs nécessitent une session authentifiée. Deux stratégies :

| Stratégie | Condition | Résultat |
|---|---|---|
| **GitHub** (recommandé) | `GITHUB_TOKEN` présent dans `.env` | URL stable `raw.githubusercontent.com/…` |
| **base64** | Pas de `GITHUB_TOKEN` | Data URI embarquée inline (volumineuse) |

Les images déjà présentes dans le repo GitHub ne sont pas ré-uploadées (déduplication par UUID).

### Notifications email (widget Échanges)

Les envois d'emails via Brevo sont pilotés par le flag `NOTIFICATIONS_ENABLED`
dans `grist_widgets/echanges/widget.js` :

```js
var NOTIFICATIONS_ENABLED = false; // ← mettre à true pour réactiver
```

Trois fonctions sont concernées : `notifyOnNewResponse`, `sendSollicitation`, `notifyAuthor`.

---

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

---

## Configuration

Copiez `.env.example` en `.env` et renseignez vos clés :

```bash
cp .env.example .env
```

| Variable | Obligatoire | Description |
|---|---|---|
| `DOCS_SESSION_ID` | ✓ | Cookie `docs_sessionid` (session navigateur) |
| `DOCS_CSRF_TOKEN` | ✓ | Cookie `csrftoken` |
| `GRIST_API_URL` | ✓ | URL de base de l'API Grist |
| `GRIST_API_KEY` | ✓ | Clé d'API Grist |
| `GRIST_DOC_ID` | ✓ | UUID du document Grist cible |
| `GITHUB_TOKEN` | — | PAT GitHub (scope `contents:write`) pour héberger les images |
| `GITHUB_REPO` | — | Repo GitHub cible (défaut : `nantodevison/docs-suite-numerique`) |
| `GITHUB_IMAGES_FOLDER` | — | Dossier images dans le repo (défaut : `images`) |
| `DOCS_BASE_URL` | — | URL de base Docs (défaut : `https://docs.numerique.gouv.fr`) |

---

## Authentification Docs (session navigateur)

L'API Docs ne fournit pas de token API direct. L'authentification repose sur
les cookies de session ProConnect.

**Prérequis : avoir une session active sur `docs.numerique.gouv.fr`.**

### Récupérer les credentials (Chrome / Edge)

1. Se connecter sur [https://docs.numerique.gouv.fr](https://docs.numerique.gouv.fr) via ProConnect
2. Ouvrir les **DevTools** (`F12`)
3. Onglet **Application** → **Cookies** → `https://docs.numerique.gouv.fr`
4. Copier :

| Cookie | Variable `.env` |
|---|---|
| `docs_sessionid` | `DOCS_SESSION_ID` |
| `csrftoken` | `DOCS_CSRF_TOKEN` |

> Les cookies expirent à la déconnexion ou après inactivité — il faudra les renouveler.

---

## Utilisation

### Script principal (CLI)

```powershell
python src/sync.py 'https://docs.numerique.gouv.fr/docs/<uuid>/'
# ou avec l'UUID seul :
python src/sync.py '<uuid>'
```

### Notebook de test (debug pas-à-pas)

Ouvrir `notebooks/test_sync.ipynb` et exécuter les cellules dans l'ordre :

| Cellule | Rôle |
|---|---|
| 1 | Imports et chargement du `.env` |
| 2 | Connexion `DocsClient` (avec GitHub token) |
| 3 | Récupération du tree |
| 4 | `flatten_tree()` en mode `json` → variable `records` |
| 5 | *(debug)* Envoi d'un record individuel |
| 6 | Aperçu DataFrame des records |
| 7 | *(diagnostic)* Vérification des émojis |
| 8 | Envoi complet vers Grist (avec `sanitize_for_waf`) |

---

## Widgets Grist

Le dossier [`grist_widgets/`](grist_widgets/) contient les widgets personnalisés
Grist (HTML/CSS/JS).

Pour les déployer sur une instance Grist sans accès internet, consulter
[`grist_widgets/README.md`](grist_widgets/README.md).
