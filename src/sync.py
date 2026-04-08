"""Script principal de synchronisation Docs → Grist."""

import os
from dotenv import load_dotenv

from docs_client import DocsClient
from grist_client import GristClient

TABLE_ID = "Documents"


def doc_to_grist_record(doc: dict) -> dict:
    """Convertit un document Docs en enregistrement Grist."""
    return {
        "fields": {
            "id": doc.get("id", ""),
            "title": doc.get("title", ""),
            "created_at": doc.get("created_at", ""),
            "updated_at": doc.get("updated_at", ""),
        }
    }


def sync() -> None:
    """Synchronise les documents Docs vers la table Grist."""
    load_dotenv()

    docs = DocsClient()
    grist = GristClient()

    print("Récupération des documents depuis Docs…")
    documents = docs.get_documents()
    print(f"  {len(documents)} document(s) trouvé(s).")

    if not documents:
        print("Aucun document à synchroniser.")
        return

    records = [doc_to_grist_record(d) for d in documents]

    print(f"Envoi de {len(records)} enregistrement(s) vers Grist…")
    grist.add_records(TABLE_ID, records)
    print("Synchronisation terminée.")


if __name__ == "__main__":
    sync()
