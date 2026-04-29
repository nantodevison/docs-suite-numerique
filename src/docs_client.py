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

    # ──────────────────────────────────────────────
    #  TRAVERSÉE ET APLATISSEMENT DU TREE
    # ──────────────────────────────────────────────

    @staticmethod
    def _strip_emojis(text: str) -> str:
        """Nettoie le texte : supprime emojis, caractères invisibles et hors-BMP."""
        import re
        # Supprime les blocs de code fencés (```lang ... ```) — déclenchent le WAF (SQL, etc.)
        text = re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.DOTALL)
        # Caractères invisibles / zero-width
        text = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff\u00ad]', '', text)
        # Espace insécable → espace normale
        text = text.replace('\xa0', ' ')
        # Emojis BMP (blocs Unicode connus)
        text = re.sub(
            r'[\u2000-\u2bff'       # Flèches, symboles divers, dingbats
            r'\u2e00-\u2e7f'        # Ponctuation supplémentaire
            r'\u3000-\u303f'        # Ponctuation CJK
            r'\ufe00-\ufe0f'        # Sélecteurs de variation
            r'\ufe30-\ufe4f]',      # Formes compatibles CJK
            '', text
        )
        # Caractères hors BMP (🌟 etc.)
        text = re.sub(r'[^\u0000-\uFFFF]', '', text)
        return text.strip()

    @staticmethod
    def _path_to_ordre(path: str) -> int:
        """
        Convertit le dernier segment de 7 caractères du path (base-36) en entier.
        Permet de trier les chapitres frères dans leur ordre natif Docs.
        """
        if not path:
            return 0
        return int(path[-7:], 36)

    def flatten_tree(self, node: dict, base_url: str,
                     parent_numero: str = None, position: int = 1,
                     is_root: bool = False) -> list[dict]:
        """
        Parcourt récursivement le tree retourné par get_tree() et retourne
        une liste de records prêts à être insérés dans Grist.

        Champs remplis : titre, niveau, ordre, numero, url, contenu.
        Champs non remplis (à compléter manuellement) :
            document, parent_chapitre, mots_cles, themes.

        Args:
            node: nœud du tree (dict avec id, title, depth, path, children…)
            base_url: URL de base de l'instance Docs (ex: https://docs.numerique.gouv.fr)
            parent_numero: numéro hiérarchique du parent (ex: "1.3"), None pour la racine
            position: position du nœud parmi ses frères (1-indexé)
            is_root: si True, le nœud racine est ignoré et ses enfants sont
                     numérotés à partir de 1 directement (Guide=1, Outils=2, etc.)

        Returns:
            list de dicts {"fields": {...}} pour l'API Grist
        """
        records = []

        doc_id = node.get("id", "")
        titre = self._strip_emojis(node.get("title", ""))
        niveau = node.get("depth", 1)
        path = node.get("path", "")

        children = node.get("children", [])
        numchild = node.get("numchild", 0)

        # Le tree ne retourne pas toujours tous les enfants (children: [] malgré numchild > 0).
        # On les récupère via fetch_children_with_content qui remonte aussi le contenu,
        # évitant ainsi un appel get_markdown() supplémentaire par enfant.
        children_content = {}
        if numchild > 0 and not children:
            try:
                raw = self.fetch_children_with_content(doc_id)
                children_content = {c["id"]: c.get("content_markdown", "") for c in raw}
                children = [
                    {
                        "id": c["id"],
                        "title": c.get("title", ""),
                        "depth": niveau + 1,
                        "path": "",
                        "numchild": 0,   # sera récupéré récursivement si besoin
                        "children": [],
                        "_content": c.get("content_markdown", ""),
                    }
                    for c in raw
                ]
            except Exception as e:
                print(f"  ⚠️  Impossible de récupérer les enfants de {doc_id} ({titre}): {e}")

        # Le nœud racine n'est pas numéroté : on traite ses enfants directement
        if is_root:
            print(f"[racine] {titre}")
            for i, child in enumerate(children, start=1):
                records.extend(
                    self.flatten_tree(child, base_url,
                                      parent_numero=None, position=i)
                )
            return records

        ordre = self._path_to_ordre(path)
        numero = f"{parent_numero}.{position}" if parent_numero else str(position)
        url = f"{base_url.rstrip('/')}/docs/{doc_id}/"

        print(f"  {'  ' * (niveau - 2)}[{numero}] {titre}")

        # Le contenu peut avoir été pré-chargé par le parent via fetch_children_with_content
        contenu = node.get("_content")
        if contenu is None:
            try:
                contenu = self.get_markdown(doc_id)
            except Exception as e:
                print(f"  ⚠️  Contenu non récupéré pour {doc_id} ({titre}): {e}")
                contenu = ""

        records.append({
            "fields": {
                "titre": titre,
                "niveau": niveau - 1,
                "ordre": ordre,
                "numero": numero,
                "url": url,
                "contenu": self._strip_emojis(contenu)[:8000],
            }
        })

        for i, child in enumerate(children, start=1):
            records.extend(
                self.flatten_tree(child, base_url,
                                  parent_numero=numero, position=i)
            )

        return records