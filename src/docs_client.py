# -*- coding: utf-8 -*-
"""Client pour l'API Docs (Suite Numérique)."""

import re
from urllib.parse import urlparse

import requests


class DocsClient:
    """Client pour interagir avec l'API Docs."""

    def __init__(self, base_url, token=None, session_id=None, csrf_token=None):
        """
        Args:
            base_url: URL de base de l'instance Docs (ex: https://docs.numerique.gouv.fr)
            token: Token OIDC Bearer (optionnel pour les documents publics)
            session_id: Cookie de session (authentification par cookie)
            csrf_token: Valeur du header X-Csrftoken (requis avec session_id)
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1.0"
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        if session_id:
            self.session.cookies.set("docs_sessionid", session_id)
        if csrf_token:
            self.session.headers["X-Csrftoken"] = csrf_token
        self.session.headers["Accept"] = "application/json"

    # ──────────────────────────────────────────────
    #  EXTRACTION D'ID DEPUIS UNE URL
    # ──────────────────────────────────────────────

    @staticmethod
    def extract_doc_id(url):
        """
        Extrait l'UUID d'un document depuis une URL Docs.

        Formats supportés :
          - https://docs.numerique.gouv.fr/docs/d9b4210e-ae68-4ca0-9667-a4624894c334/
          - https://docs.numerique.gouv.fr/docs/d9b4210e-ae68-4ca0-9667-a4624894c334
          - Juste un UUID brut

        Returns:
            str: UUID du document, ou None si non trouvé
        """
        if not url:
            return None

        # UUID brut ?
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        if re.fullmatch(uuid_pattern, url.strip(), re.IGNORECASE):
            return url.strip()

        # Cherche dans le path de l'URL
        match = re.search(uuid_pattern, url, re.IGNORECASE)
        return match.group(0) if match else None

    # ──────────────────────────────────────────────
    #  RÉCUPÉRER LES MÉTADONNÉES D'UN DOCUMENT
    # ──────────────────────────────────────────────

    def get_document(self, doc_id):
        """
        Récupère les métadonnées d'un document.

        Returns:
            dict avec id, title, created_at, updated_at, etc.
        """
        resp = self.session.get(f"{self.api_url}/documents/{doc_id}/")
        resp.raise_for_status()
        return resp.json()

    # ──────────────────────────────────────────────
    #  RÉCUPÉRER LE CONTENU (MARKDOWN / HTML / JSON)
    # ──────────────────────────────────────────────

    def get_content(self, doc_id, content_format="markdown"):
        """
        Récupère le contenu d'un document dans le format demandé.

        L'API utilise un service de conversion interne (Y-Provider)
        pour convertir le format Yjs natif vers markdown/html/json.

        Args:
            doc_id: UUID du document
            content_format: 'markdown', 'html', ou 'json'

        Returns:
            dict avec id, title, content, created_at, updated_at
        """
        if content_format not in ("markdown", "html", "json"):
            raise ValueError("content_format doit être 'markdown', 'html' ou 'json'")

        resp = self.session.get(
            f"{self.api_url}/documents/{doc_id}/content/",
            params={"content_format": content_format},
        )
        resp.raise_for_status()
        return resp.json()

    def get_markdown(self, doc_id):
        """Raccourci pour get_content en markdown."""
        data = self.get_content(doc_id, "markdown")
        return data.get("content", "")

    # ──────────────────────────────────────────────
    #  LISTE DES SOUS-DOCUMENTS (ENFANTS)
    # ──────────────────────────────────────────────

    def get_children(self, doc_id, page=1, page_size=100):
        """
        Récupère les enfants directs d'un document.

        Endpoint: GET /documents/{id}/children/
        Paginé.

        Returns:
            dict avec count, next, previous, results
        """
        resp = self.session.get(
            f"{self.api_url}/documents/{doc_id}/children/",
            params={"page": page, "page_size": page_size},
        )
        resp.raise_for_status()
        return resp.json()

    def get_all_children(self, doc_id):
        """
        Récupère TOUS les enfants directs (dépagination automatique).

        Returns:
            list de documents
        """
        all_results = []
        page = 1
        while True:
            data = self.get_children(doc_id, page=page)
            all_results.extend(data.get("results", []))
            if not data.get("next"):
                break
            page += 1
        return all_results

    # ──────────────────────────────────────────────
    #  ARBRE COMPLET
    # ──────────────────────────────────────────────

    def get_tree(self, doc_id):
        """
        Récupère l'arbre hiérarchique du document.

        Endpoint: GET /documents/{id}/tree/
        Retourne une structure imbriquée avec les ancêtres et enfants.

        Returns:
            dict imbriqué
        """
        resp = self.session.get(f"{self.api_url}/documents/{doc_id}/tree/")
        resp.raise_for_status()
        return resp.json()

    # ──────────────────────────────────────────────
    #  UTILITAIRE : RÉCUPÉRER TOUT D'UN COUP
    # ──────────────────────────────────────────────

    def fetch_document_with_content(self, url_or_id):
        """
        À partir d'une URL ou d'un UUID :
        1. Extrait l'ID
        2. Récupère les métadonnées
        3. Récupère le contenu markdown

        Returns:
            dict avec id, title, content_markdown, created_at, updated_at
        """
        doc_id = self.extract_doc_id(url_or_id)
        if not doc_id:
            raise ValueError(f"Impossible d'extraire un UUID depuis : {url_or_id}")

        metadata = self.get_document(doc_id)
        content_data = self.get_content(doc_id, "markdown")

        return {
            "id": doc_id,
            "title": metadata.get("title", ""),
            "content_markdown": content_data.get("content", ""),
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("updated_at"),
        }

    def fetch_children_with_content(self, parent_url_or_id):
        """
        Récupère tous les enfants d'un doc parent avec leur contenu markdown.

        Returns:
            list de dicts avec id, title, content_markdown, ...
        """
        parent_id = self.extract_doc_id(parent_url_or_id)
        if not parent_id:
            raise ValueError(f"Impossible d'extraire un UUID depuis : {parent_url_or_id}")

        children = self.get_all_children(parent_id)
        results = []
        for child in children:
            child_id = child["id"]
            try:
                content_data = self.get_content(child_id, "markdown")
                results.append({
                    "id": child_id,
                    "title": child.get("title", ""),
                    "content_markdown": content_data.get("content", ""),
                    "created_at": child.get("created_at"),
                    "updated_at": child.get("updated_at"),
                })
            except requests.HTTPError as e:
                print(f"⚠️  Erreur pour {child_id} ({child.get('title')}): {e}")
                results.append({
                    "id": child_id,
                    "title": child.get("title", ""),
                    "content_markdown": None,
                    "error": str(e),
                })
        return results