"""Script principal de synchronisation Docs → Grist."""

import os
from urllib.parse import urlparse
from dotenv import load_dotenv

from docs_client import DocsClient
from grist_client import GristClient

TABLE_CHAPITRES = "Chapitres"


# ──────────────────────────────────────────────
#  SYNC PRINCIPALE
# ──────────────────────────────────────────────

def sync_chapitres(root_url_or_id: str) -> None:
    """
    Synchronise les chapitres d'un document Docs vers la table Grist 'Chapitres'.

    Args:
        root_url_or_id: URL ou UUID du document racine Docs
    """
    load_dotenv()

    base_url = os.environ.get("DOCS_API_URL", "https://docs.numerique.gouv.fr")
    parsed = urlparse(base_url)
    docs_base = f"{parsed.scheme}://{parsed.netloc}"

    docs = DocsClient(
        base_url=docs_base,
        session_id=os.environ.get("DOCS_SESSION_ID"),
        csrf_token=os.environ.get("DOCS_CSRF_TOKEN"),
    )
    grist = GristClient()

    print(f"Récupération du tree depuis Docs : {root_url_or_id}")
    tree = docs.get_tree(DocsClient.extract_doc_id(root_url_or_id))
    print(f"  Racine : {tree.get('title', '')}\n")

    print("Traversée de l'arbre et récupération des contenus…")
    records = docs.flatten_tree(tree, docs_base, is_root=True)
    print(f"\n  {len(records)} chapitre(s) à synchroniser.")

    print(f"\nEnvoi vers Grist (table '{TABLE_CHAPITRES}')…")
    grist.add_records(TABLE_CHAPITRES, records)
    print("Synchronisation terminée.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage : python sync.py <url_ou_uuid_du_document_racine>")
        sys.exit(1)
    sync_chapitres(sys.argv[1])
