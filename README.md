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

## Utilisation

```bash
python src/sync.py
```
