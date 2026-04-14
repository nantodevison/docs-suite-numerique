"""Script principal de synchronisation Docs → Grist.

Usage :
    python sync.py <url_ou_uuid_du_document_racine>

Variables d'environnement requises (fichier .env) :
    DOCS_SESSION_ID     Cookie de session Docs
    DOCS_CSRF_TOKEN     Header CSRF Docs
    GRIST_API_URL       URL de base de l'API Grist
    GRIST_API_KEY       Clé API Grist
    GRIST_DOC_ID        UUID du document Grist cible

Variables optionnelles :
    DOCS_BASE_URL       URL de base de l'instance Docs
                        (défaut : https://docs.numerique.gouv.fr)
    GITHUB_TOKEN        PAT GitHub (scope contents:write) pour héberger
                        les images internes Docs en public sur GitHub.
                        Sans ce token, les images sont embarquées en base64.
    GITHUB_REPO         Repo GitHub cible (défaut : nantodevison/docs-suite-numerique)
    GITHUB_IMAGES_FOLDER Dossier images dans le repo (défaut : images)
"""

import os
import sys

from dotenv import load_dotenv

from docs_client import DocsClient
from grist_client import GristClient

# ──────────────────────────────────────────────
#  CONSTANTES
# ──────────────────────────────────────────────

TABLE_CHAPITRES = "Chapitres"
GRIST_COLUMNS = {"titre", "niveau", "ordre", "numero", "url", "contenu"}
CONTENT_FORMAT = "json"   # 'json' | 'markdown' | 'html' | 'auto'


# ──────────────────────────────────────────────
#  SYNC PRINCIPALE
# ──────────────────────────────────────────────

def sync_chapitres(root_url_or_id: str) -> tuple[list, list]:
    """Synchronise les chapitres d'un document Docs vers la table Grist.

    Étapes :
        1. Récupération du tree Docs depuis root_url_or_id
        2. Aplatissement récursif → records (contenu JSON→Markdown,
           images internes uploadées sur GitHub si GITHUB_TOKEN présent)
        3. Sanitisation WAF (suppression des blocs SQL du contenu)
        4. Envoi vers Grist via send_records()

    Args:
        root_url_or_id: URL ou UUID du document racine Docs.

    Returns:
        tuple (ok, ko) retourné par GristClient.send_records().
    """
    load_dotenv()

    docs_base = os.environ.get("DOCS_BASE_URL", "https://docs.numerique.gouv.fr")
    github_repo = os.environ.get("GITHUB_REPO", "nantodevison/docs-suite-numerique")
    github_folder = os.environ.get("GITHUB_IMAGES_FOLDER", "images")

    # ── Clients ──────────────────────────────────────────────────────────────
    docs = DocsClient(
        base_url=docs_base,
        session_id=os.environ.get("DOCS_SESSION_ID"),
        csrf_token=os.environ.get("DOCS_CSRF_TOKEN"),
        github_token=os.environ.get("GITHUB_TOKEN"),
        github_repo=github_repo,
        github_images_folder=github_folder,
    )
    grist = GristClient()

    # ── 1. Tree ───────────────────────────────────────────────────────────────
    print(f"\n{'─' * 60}")
    print(f"  Docs → Grist  |  table : {TABLE_CHAPITRES}")
    print(f"{'─' * 60}")
    doc_id = DocsClient.extract_doc_id(root_url_or_id)
    if not doc_id:
        print(f"[ERREUR] Impossible d'extraire un UUID depuis : {root_url_or_id}")
        sys.exit(1)

    print(f"\n[1/3] Récupération du tree Docs…")
    tree = docs.get_tree(doc_id)
    print(f"  Racine : {tree.get('title', '')}")

    # ── 2. Aplatissement ─────────────────────────────────────────────────────
    print(f"\n[2/3] Aplatissement et récupération des contenus ({CONTENT_FORMAT})…")
    records = docs.flatten_tree(
        tree,
        docs_base,
        is_root=True,
        content_format=CONTENT_FORMAT,
    )
    print(f"\n  → {len(records)} record(s) construits.")

    # ── 3. Sanitisation WAF ───────────────────────────────────────────────────
    records_clean = [
        {**r, "fields": {
            **r["fields"],
            "contenu": DocsClient.sanitize_for_waf(r["fields"].get("contenu", ""))
            if isinstance(r["fields"].get("contenu"), str)
            else r["fields"].get("contenu", ""),
        }}
        for r in records
    ]

    # ── 4. Envoi Grist ────────────────────────────────────────────────────────
    print(f"\n[3/3] Envoi vers Grist (table '{TABLE_CHAPITRES}')…")
    ok, ko = grist.send_records(TABLE_CHAPITRES, records_clean, columns=GRIST_COLUMNS)

    print(f"\n{'─' * 60}")
    print(f"  Synchronisation terminée : {len(ok)} ✓  {len(ko)} ✗")
    print(f"{'─' * 60}\n")

    return ok, ko


# ──────────────────────────────────────────────
#  POINT D'ENTRÉE
# ──────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sync_chapitres(sys.argv[1])
