# docs-suite-numerique

Synchronisation des documents de la **Suite Numérique – Docs** vers **Grist**.

## Structure du projet

```
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
└── src/
    ├── __init__.py
    ├── docs_client.py   # Client API Docs
    ├── grist_client.py  # Client API Grist
    └── sync.py          # Script principal
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Copiez `.env.example` en `.env` et renseignez vos clés d'API :

```bash
cp .env.example .env
```

| Variable         | Description                          |
|-----------------|--------------------------------------|
| `DOCS_API_URL`  | URL de base de l'API Docs            |
| `DOCS_API_KEY`  | Clé d'API Docs                       |
| `GRIST_API_URL` | URL de base de l'API Grist           |
| `GRIST_API_KEY` | Clé d'API Grist                      |
| `GRIST_DOC_ID`  | Identifiant du document Grist cible  |

## Authentification Docs (session navigateur)

L'API Docs de la Suite Numérique ne fournit pas de token API direct. L'authentification repose sur les cookies de session créés lors d'une connexion via ProConnect dans le navigateur.

**Prérequis : avoir une session active sur `docs.numerique.gouv.fr`.**

### Récupérer les credentials depuis le navigateur (Chrome / Edge)

1. Connecte-toi sur [https://docs.numerique.gouv.fr](https://docs.numerique.gouv.fr) via ProConnect
2. Ouvre les **DevTools** avec `F12`
3. Va dans l'onglet **Appli** (ou *Application*)
4. Dans le menu gauche : **Stockage** → **Cookies** → sélectionne `https://docs.numerique.gouv.fr`
5. Copie les valeurs de ces deux cookies :

| Cookie | Description |
|---|---|
| `docs_sessionid` | Identifiant de session (à passer en `session_id`) |
| `csrftoken` | Jeton CSRF (à passer en `csrf_token`) |

### Utilisation dans le code

```python
from src.docs_client import DocsClient

client = DocsClient(
    "https://docs.numerique.gouv.fr",
    session_id="<valeur de docs_sessionid>",
    csrf_token="<valeur de csrftoken>"
)
result = client.fetch_document_with_content("https://docs.numerique.gouv.fr/docs/<uuid>/")
```

> **Note :** les cookies expirent dès que tu te déconnectes ou après un délai d'inactivité. Il faudra alors en récupérer de nouveaux depuis DevTools.

## Utilisation

```bash
python src/sync.py
```
