"""Client API pour la Suite Numérique – Docs."""

import os
import requests


class DocsClient:
    """Client HTTP pour l'API Docs de la Suite Numérique."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None):
        self.api_url = (api_url or os.environ.get("DOCS_API_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("DOCS_API_KEY", "")
        if not self.api_url:
            raise ValueError("DOCS_API_URL est requis.")
        if not self.api_key:
            raise ValueError("DOCS_API_KEY est requis.")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def get_documents(self) -> list[dict]:
        """Retourne la liste de tous les documents accessibles."""
        response = self.session.get(f"{self.api_url}/documents/")
        response.raise_for_status()
        return response.json()

    def get_document(self, document_id: str) -> dict:
        """Retourne les détails d'un document par son identifiant."""
        response = self.session.get(f"{self.api_url}/documents/{document_id}/")
        response.raise_for_status()
        return response.json()
