# -*- coding: utf-8 -*-
"""Client pour l'API Docs (Suite Numérique)."""

import base64 as _base64
import re
from html.parser import HTMLParser
from mimetypes import guess_type as _guess_type
from urllib.parse import urlparse

import requests

# ──────────────────────────────────────────────
#  DÉTECTION D'ÉMOJIS
# ──────────────────────────────────────────────

# Couvre les plages Unicode utilisées pour les émojis courants.
# Reproduit la logique de la lib `emoji-regex` utilisée côté frontend Docs
# (cf. src/frontend/.../doc-management/utils.ts → getEmojiAndTitle).
_EMOJI_RE = re.compile(
    r"(?:"
    r"[\U0001F000-\U0001FFFF]"   # Emojis modernes (visages, objets, voyages…)
    r"|[\U00002600-\U000027BF]"  # Symboles divers, météo, dingbats
    r"|[\U0001F900-\U0001FA9F]"  # Symboles supplémentaires
    r"|[\U00002B50-\U00002B55]"  # Étoiles
    r"|[\U000025FB-\U000025FE]"  # Carrés géométriques
    r"|[\U00003030\U0000303D]"   # CJK
    r")"
    r"[\U0001F3FB-\U0001F3FF]?"  # Modificateurs de teint (Fitzpatrick)
    r"(?:\u200D(?:"              # ZWJ sequence
    r"[\U0001F000-\U0001FFFF]"
    r"|[\U00002600-\U000027BF]"
    r")[\U0001F3FB-\U0001F3FF]?)*"
    r"\uFE0F?",                  # Sélecteur de variation
    re.UNICODE,
)


# ──────────────────────────────────────────────
#  SUPPRESSION DES BLOCS DE CODE MARKDOWN
# ──────────────────────────────────────────────

# Supprime les blocs ``` … ``` (SQL, Python, bash…) pour éviter les faux
# positifs WAF (Incapsula bloque les POST contenant du SQL notamment).
_CODE_BLOCK_RE = re.compile(r'```[^\n]*\n.*?```', re.DOTALL)

# Langages SQL à neutraliser avant envoi vers Grist (le WAF Incapsula bloque
# les POST contenant du code SQL).
WAF_SQL_LANGUAGES: list[str] = [
    'sql', 'postgresql', 'postgres', 'psql', 'plpgsql',
    'mysql', 'sqlite', 'tsql', 'mariadb',
]


# ──────────────────────────────────────────────
#  CONVERTISSEUR HTML → TEXTE
# ──────────────────────────────────────────────

class _HTMLTextExtractor(HTMLParser):
    """Extrait le texte brut d'un fragment HTML en préservant les émojis."""

    _BLOCK_TAGS = frozenset(
        ["p", "div", "br", "li", "tr", "th", "td",
         "h1", "h2", "h3", "h4", "h5", "h6",
         "blockquote", "pre", "section", "article"]
    )
    _SKIP_TAGS = frozenset(["script", "style"])

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self._BLOCK_TAGS and self._parts and self._parts[-1] != "\n":
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        # Collapse consecutive newlines to max 2
        text = "".join(self._parts)
        return re.sub(r"\n{3,}", "\n\n", text).strip()


class DocsClient:
    """Client pour interagir avec l'API Docs."""

    def __init__(self, base_url, token=None, session_id=None, csrf_token=None,
                 github_token=None, github_repo="nantodevison/docs-suite-numerique",
                 github_images_branch="master", github_images_folder="images"):
        """
        Args:
            base_url: URL de base de l'instance Docs (ex: https://docs.numerique.gouv.fr)
            token: Token OIDC Bearer (optionnel pour les documents publics)
            session_id: Cookie de session (authentification par cookie)
            csrf_token: Valeur du header X-Csrftoken (requis avec session_id)
            github_token: PAT GitHub avec scope contents:write (optionnel).
                Si fourni, embed_internal_images() utilisera GitHub comme hôte
                d'images plutôt que le base64 (moins volumineux, URL stable).
            github_repo: Repo GitHub cible, format 'owner/repo'.
            github_images_branch: Branche où stocker les images.
            github_images_folder: Dossier dans le repo (ex: 'images').
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
        # GitHub image hosting
        self._github_token = github_token
        self._github_repo = github_repo
        self._github_images_branch = github_images_branch
        self._github_images_folder = github_images_folder.strip("/")

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

        # HTTP 500 du Y-Provider : le contenu Yjs existe mais n'est pas
        # convertible (document trop minimal, structure corrompue, etc.).
        # On traite ce cas comme un contenu vide plutôt que de planter.
        if resp.status_code == 500:
            print(f"    ⚠️  Y-Provider 500 pour {doc_id} [{content_format}] "
                  f"— contenu non convertible, traité comme vide.")
            return {"content": ""}

        resp.raise_for_status()
        return resp.json()

    def get_markdown(self, doc_id):
        """Raccourci pour get_content en markdown."""
        data = self.get_content(doc_id, "markdown")
        # Utilise `or ""` et non `.get("content", "")` : si l'API renvoie
        # {"content": null} (document vide), .get() retourne None (la clé
        # existe) — le défaut "" ne s'applique que quand la clé est absente.
        return data.get("content") or ""

    def get_html(self, doc_id):
        """Raccourci pour get_content en HTML."""
        data = self.get_content(doc_id, "html")
        return data.get("content") or ""

    def get_markdown_with_emoji_fallback(self, doc_id):
        """
        Récupère le contenu en markdown.

        Si la conversion markdown échoue (erreur Y-Provider sur des nœuds
        emoji BlockNote, par exemple), tente une récupération en HTML puis
        convertit en texte brut — ce qui préserve les émojis Unicode.

        Returns:
            tuple(str, str): (contenu, format_utilisé)
                format_utilisé vaut 'markdown', 'html' ou 'erreur'
        """
        # --- Tentative 1 : markdown ---
        try:
            md = self.get_markdown(doc_id)
            if md is not None:
                return md, "markdown"
        except requests.HTTPError as exc:
            print(f"    ↳ Markdown KO ({exc.response.status_code}), "
                  f"tentative HTML…")
        except Exception as exc:  # noqa: BLE001
            print(f"    ↳ Markdown KO ({exc!s}), tentative HTML…")

        # --- Tentative 2 : HTML → texte ---
        try:
            html = self.get_html(doc_id)
            if html:
                text = self.html_to_text(html)
                return text, "html"
        except Exception as exc:  # noqa: BLE001
            print(f"    ↳ HTML KO ({exc!s})")

        return "", "erreur"

    def get_content_all_formats(self, doc_id: str) -> dict:
        """
        Récupère le contenu dans les trois formats disponibles.

        Utile pour diagnostiquer comment les émojis sont représentés :
        le format JSON (BlockNote) montre la structure brute avec les nœuds
        emoji ; le format HTML les exprime souvent mieux que le markdown.

        Returns:
            dict avec les clés 'markdown', 'html', 'json',
            et '<format>_error' en cas d'échec.
        """
        results: dict = {}
        for fmt in ("markdown", "html", "json"):
            try:
                data = self.get_content(doc_id, fmt)
                results[fmt] = data.get("content") or ""
            except Exception as exc:  # noqa: BLE001
                results[fmt] = None
                results[f"{fmt}_error"] = str(exc)
        return results

    def get_json_blocks(self, doc_id: str) -> list[dict]:
        """Récupère le contenu d'un document en JSON BlockNote (tableau de blocs).

        Contrairement à content_format=markdown, ce format retourne la structure
        brute des blocs *avant* sérialisation par le Y-Provider — les blocs custom
        (callout, etc.) sont présents avec leur type et props réels.

        Returns:
            list de blocs BlockNote (chacun avec id, type, props, content, children)
        """
        data = self.get_content(doc_id, "json")
        content = data.get("content")
        if not content:
            return []
        if isinstance(content, list):
            return content
        # Fallback : si l'API renvoie une chaîne JSON (ne devrait pas arriver)
        import json as _json
        try:
            parsed = _json.loads(content)
            return parsed if isinstance(parsed, list) else []
        except Exception:  # noqa: BLE001
            return []

    def get_markdown_from_json(self, doc_id: str) -> tuple[str, str]:
        """Récupère le contenu via JSON BlockNote et le convertit en markdown standard.

        Avantages par rapport à content_format=markdown :
        — Les blocs custom (callout, etc.) sont rendus correctement.
        — Aucune perte de contenu liée à un schéma BlockNote non supporté
          par le Y-Provider (ex: callout → blockquote, inline custom → texte brut).

        Returns:
            tuple(str, str): (contenu_markdown, format_utilisé)
                format_utilisé vaut 'json→md' ou 'erreur'
        """
        try:
            blocks = self.get_json_blocks(doc_id)
            n_lost = self._count_internal_refs_lost(blocks)
            if n_lost:
                print(f"    ⚠️  {n_lost} référence(s) interne(s) non résolue(s) "
                      f"(placeholder '[référence interne]' inséré)")
            md = self.blocknote_to_markdown(blocks)
            md = self.embed_internal_images(md)
            return md, "json→md"
        except Exception as exc:  # noqa: BLE001
            print(f"    ↳ JSON→MD KO ({exc!s})")
            return "", "erreur"

    # ──────────────────────────────────────────────
    #  UTILITAIRES STATIQUES
    # ──────────────────────────────────────────────

    def _fetch_as_data_uri(self, url: str) -> str | None:
        """Télécharge une image via la session authentifiée et retourne une data URI.

        Utilisé pour embarquer les images internes Docs (stockées sous /media/…)
        en base64, afin qu'elles soient autonomes sans session active (ex: Grist).

        Returns:
            str data URI ("data:image/png;base64,…") ou None si échec.
        """
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            mime = resp.headers.get("Content-Type", "").split(";")[0].strip()
            if not mime or not mime.startswith("image/"):
                guessed, _ = _guess_type(url)
                mime = guessed or "image/png"
            b64 = _base64.b64encode(resp.content).decode("ascii")
            return f"data:{mime};base64,{b64}"
        except Exception as exc:  # noqa: BLE001
            print(f"    ⚠️  Image non téléchargeable ({url}): {exc}")
            return None

    def _ensure_image_in_github(self, url: str) -> str | None:
        """Upload une image interne Docs dans le repo GitHub et retourne sa raw URL.

        L'UUID de la pièce jointe Docs est utilisé comme nom de fichier, ce qui
        garantit la déduplication : si l'image est déjà présente dans le repo,
        elle n'est pas ré-uploadée.

        Returns:
            Raw GitHub URL (https://raw.githubusercontent.com/…) ou None si échec.
        """
        if not self._github_token:
            return None

        # Extrait l'UUID de la pièce jointe depuis l'URL Docs
        # Format : /media/{doc_id}/attachments/{attachment_uuid}.{ext}
        m = re.search(r'/attachments/([\w-]+)(\.[a-zA-Z0-9]+)?$', url)
        if not m:
            print(f"    ⚠️  Impossible d'extraire l'UUID de l'image ({url})")
            return None
        attachment_uuid = m.group(1)
        ext = m.group(2) or ""
        path_in_repo = f"{self._github_images_folder}/{attachment_uuid}{ext}"

        gh_api = f"https://api.github.com/repos/{self._github_repo}/contents/{path_in_repo}"
        gh_headers = {
            "Authorization": f"Bearer {self._github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # Vérifie si le fichier existe déjà (déduplication)
        check = requests.get(gh_api, headers=gh_headers, timeout=10)
        if check.status_code == 200:
            # Déjà présent — retourne directement la raw URL
            raw_url = (f"https://raw.githubusercontent.com/{self._github_repo}"
                       f"/{self._github_images_branch}/{path_in_repo}")
            return raw_url

        # Télécharge depuis Docs (session authentifiée)
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            print(f"    ⚠️  Image non téléchargeable depuis Docs ({url}): {exc}")
            return None

        # Upload vers GitHub
        content_b64 = _base64.b64encode(resp.content).decode("ascii")
        payload = {
            "message": f"chore: add Docs attachment {attachment_uuid}",
            "content": content_b64,
            "branch": self._github_images_branch,
        }
        try:
            put = requests.put(gh_api, headers=gh_headers, json=payload, timeout=30)
            put.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            print(f"    ⚠️  Upload GitHub échoué ({path_in_repo}): {exc}")
            return None

        raw_url = (f"https://raw.githubusercontent.com/{self._github_repo}"
                   f"/{self._github_images_branch}/{path_in_repo}")
        return raw_url

    def embed_internal_images(self, text: str, strategy: str = "auto") -> str:
        """Remplace les URLs d'images internes Docs par des URLs autonomes.

        Les pièces jointes uploadées dans Docs nécessitent une authentification.
        Cette méthode les rend accessibles sans session via deux stratégies :

        Args:
            strategy:
                'auto'   : GitHub si github_token configuré, sinon base64
                'github' : stocke dans le repo GitHub, retourne une raw URL
                'base64' : embarque en data URI base64 (autonome, mais volumineux)

        Seules les URLs internes (sous self.base_url/media/) sont traitées.
        Les images externes sont conservées telles quelles.
        """
        use_github = (strategy == "github" or
                      (strategy == "auto" and bool(self._github_token)))

        base = re.escape(self.base_url)
        _md_re = re.compile(r'!\[([^\]]*)\]\((' + base + r'/media/[^)\s]+)\)')
        _html_re = re.compile(r'(<img[^>]+src=")(' + base + r'/media/[^"]+)(")')

        def _resolve(url: str) -> str | None:
            if use_github:
                return self._ensure_image_in_github(url)
            return self._fetch_as_data_uri(url)

        def _replace_md(m: re.Match) -> str:
            resolved = _resolve(m.group(2))
            return f"![{m.group(1)}]({resolved})" if resolved else m.group(0)

        def _replace_html(m: re.Match) -> str:
            resolved = _resolve(m.group(2))
            return f"{m.group(1)}{resolved}{m.group(3)}" if resolved else m.group(0)

        text = _md_re.sub(_replace_md, text)
        text = _html_re.sub(_replace_html, text)
        return text

    @staticmethod
    def html_to_text(html_content: str) -> str:
        """
        Convertit du HTML en texte brut en préservant les émojis Unicode.

        Utilise uniquement la stdlib Python (html.parser) — pas de dépendance
        externe.
        """
        parser = _HTMLTextExtractor()
        parser.feed(html_content)
        return parser.get_text()

    @staticmethod
    def extract_emoji_from_title(title: str) -> tuple:
        """
        Sépare l'émoji de tête du reste du titre, comme le fait le frontend
        Docs (cf. utils.ts → getEmojiAndTitle).

        Args:
            title: titre complet (ex: "🎉 Mon document")

        Returns:
            (emoji, titre_propre)
                emoji      : chaîne de l'émoji (ou None si absent)
                titre_propre : titre sans l'émoji et sans espaces superflus
        """
        if not title:
            return None, title or ""

        stripped = title.lstrip()
        m = _EMOJI_RE.match(stripped)
        if m and stripped.startswith(m.group(0)):
            emoji = m.group(0)
            clean = stripped[len(emoji):].strip()
            return emoji, clean

        return None, title

    @staticmethod
    def count_emojis(text: str) -> int:
        """Compte le nombre d'émojis dans un texte."""
        return len(_EMOJI_RE.findall(text or ""))

    @staticmethod
    def strip_code_blocks(text: str, languages: list[str] | None = None) -> str:
        """Supprime les blocs de code markdown (``` … ```) d'un texte.

        Args:
            text     : texte à nettoyer.
            languages: si fourni, seuls les blocs dont l'identifiant de
                       langage est dans cette liste sont supprimés (insensible
                       à la casse). Si None, TOUS les blocs sont supprimés.

        Exemples :
            # Supprime uniquement les blocs SQL (risque WAF)
            DocsClient.strip_code_blocks(text, languages=['sql', 'postgresql'])
            # Supprime tous les blocs (comportement d'origine)
            DocsClient.strip_code_blocks(text)

        Note : les blocs 'callout', 'image', etc. de BlockNote sont sérialisés
        en markdown sous forme de blocs fencés avec leur type comme langage.
        Éviter de les supprimer pour ne pas perdre du contenu légitime.
        """
        if not text:
            return ""
        if languages is None:
            return _CODE_BLOCK_RE.sub('[bloc de code supprimé]', text)
        lang_alt = '|'.join(re.escape(lang) for lang in languages)
        targeted_re = re.compile(
            rf'```(?:{lang_alt})[ \t]*\n.*?```',
            re.DOTALL | re.IGNORECASE,
        )
        return targeted_re.sub('[bloc de code supprimé]', text)

    @staticmethod
    def sanitize_for_waf(text: str) -> str:
        """Supprime les blocs de code SQL du markdown pour éviter les blocages WAF.

        Le WAF Incapsula bloque les POST contenant du SQL. Cette méthode applique
        `strip_code_blocks` avec la liste `WAF_SQL_LANGUAGES` définie au niveau
        module — les autres langages (Python, bash, etc.) sont conservés.
        """
        return DocsClient.strip_code_blocks(text, languages=WAF_SQL_LANGUAGES)

    @staticmethod
    def _count_internal_refs_lost(blocks: list[dict]) -> int:
        """Compte récursivement les éléments de liste dont le contenu est vide.

        Un élément de liste à contenu vide (content: []) indique qu'une
        référence interne Docs (@mention) était présente mais a été supprimée
        silencieusement par le Y-Provider lors de la sérialisation JSON.
        Ces éléments sont rendus par _render_block avec le placeholder
        '[référence interne]'.

        Returns:
            Nombre d'éléments affectés.
        """
        count = 0
        for b in blocks:
            btype = b.get("type", "")
            if btype in ("bulletListItem", "numberedListItem", "checkListItem"):
                content = b.get("content", [])
                if isinstance(content, list):
                    has_text = any(
                        i.get("type") == "text" and i.get("text", "").strip()
                        for i in content
                    )
                    has_link = any(i.get("type") == "link" for i in content)
                    if not has_text and not has_link and not b.get("children"):
                        count += 1
            count += DocsClient._count_internal_refs_lost(b.get("children", []))
        return count

    # ──────────────────────────────────────────────
    #  CONVERTISSEUR BLOCKNOTE JSON → MARKDOWN
    # ──────────────────────────────────────────────

    @staticmethod
    def _render_inline(inline_items: list) -> str:
        """Convertit une liste d'inline content BlockNote en texte markdown."""
        parts = []
        for item in (inline_items or []):
            itype = item.get("type", "text")
            if itype == "text":
                text = item.get("text", "")
                styles = item.get("styles", {})
                # Code : ne pas combiner avec bold/italic
                if styles.get("code"):
                    parts.append(f"`{text}`")
                    continue
                if styles.get("bold") and styles.get("italic"):
                    text = f"***{text}***"
                elif styles.get("bold"):
                    text = f"**{text}**"
                elif styles.get("italic"):
                    text = f"*{text}*"
                if styles.get("strikethrough"):
                    text = f"~~{text}~~"
                parts.append(text)
            elif itype == "link":
                link_text = DocsClient._render_inline(item.get("content", []))
                href = item.get("href", "")
                if not link_text:
                    # Lien interne Docs : le titre est résolu dynamiquement par
                    # le frontend — le JSON ne contient pas de texte visible.
                    # Fallback : on affiche l'URL brute.
                    link_text = href
                parts.append(f"[{link_text}]({href})")
            else:
                # Inline custom inconnu (mention, etc.) — extraction best-effort
                # Priorité : content récursif → text → props (strings) → attrs
                sub = item.get("content", [])
                if isinstance(sub, list) and sub:
                    parts.append(DocsClient._render_inline(sub))
                elif isinstance(sub, str) and sub:
                    parts.append(sub)
                elif item.get("text"):
                    parts.append(str(item["text"]))
                else:
                    # Dernier recours : valeurs string non-vides des props
                    # (couvre les mentions, références internes, etc.)
                    props = item.get("props", {})
                    prop_texts = [
                        str(v) for v in props.values()
                        if isinstance(v, str) and v
                    ]
                    if prop_texts:
                        parts.append(" ".join(prop_texts))
        return "".join(parts)

    @staticmethod
    def _render_inline_html(inline_items: list) -> str:
        """Convertit une liste d'inline content BlockNote en HTML.

        Utilisé pour les cellules de tableaux avec rowspan/colspan, où le
        Markdown pipe table ne peut pas représenter les fusions.
        """
        parts = []
        for item in (inline_items or []):
            itype = item.get("type", "text")
            if itype == "text":
                text = item.get("text", "")
                styles = item.get("styles", {})
                if styles.get("code"):
                    parts.append(f"<code>{text}</code>")
                    continue
                if styles.get("bold") and styles.get("italic"):
                    text = f"<strong><em>{text}</em></strong>"
                elif styles.get("bold"):
                    text = f"<strong>{text}</strong>"
                elif styles.get("italic"):
                    text = f"<em>{text}</em>"
                if styles.get("strikethrough"):
                    text = f"<del>{text}</del>"
                parts.append(text)
            elif itype == "link":
                link_html = DocsClient._render_inline_html(item.get("content", []))
                href = item.get("href", "")
                if not link_html:
                    link_html = href
                parts.append(f'<a href="{href}">{link_html}</a>')
            else:
                sub = item.get("content", [])
                if isinstance(sub, list) and sub:
                    parts.append(DocsClient._render_inline_html(sub))
                elif item.get("text"):
                    parts.append(str(item["text"]))
        return "".join(parts)

    @staticmethod
    def _render_block(block: dict, indent: int = 0) -> str:
        """Convertit un bloc BlockNote en markdown (récursif pour les enfants)."""
        btype = block.get("type", "paragraph")
        props = block.get("props", {})
        content = block.get("content", [])
        children = block.get("children", [])

        pad = "  " * indent

        # Texte inline du bloc courant
        inline = DocsClient._render_inline(content) if isinstance(content, list) else ""

        # Enfants (listes imbriquées, etc.) — on filtre les rendus vides
        child_lines = [r for r in
                       (DocsClient._render_block(ch, indent + 1) for ch in children)
                       if r]
        children_str = ("\n" + "\n".join(child_lines)) if child_lines else ""

        if btype == "heading":
            level = min(max(int(props.get("level", 1)), 1), 6)
            return f"{pad}{'#' * level} {inline}{children_str}"

        elif btype == "bulletListItem":
            # Contenu vide : l'élément existait mais sa référence interne
            # (@mention Docs) a été supprimée silencieusement par le Y-Provider.
            display = inline if inline else "[référence interne]"
            return f"{pad}* {display}{children_str}"

        elif btype == "numberedListItem":
            display = inline if inline else "[référence interne]"
            return f"{pad}1. {display}{children_str}"

        elif btype == "checkListItem":
            box = "x" if props.get("checked") else " "
            display = inline if inline else "[référence interne]"
            return f"{pad}- [{box}] {display}{children_str}"

        elif btype == "codeBlock":
            lang = props.get("language", "")
            return f"{pad}```{lang}\n{inline}\n{pad}```{children_str}"

        elif btype == "callout":
            # Rendu en blockquote markdown avec l'émoji en préfixe de la première ligne
            emoji = props.get("emoji", "")
            prefix = f"{emoji} " if emoji else ""
            bq_lines = []
            for i, line in enumerate(inline.split("\n")):
                bq_lines.append(f"{pad}> {prefix if i == 0 else ''}{line}")
            for line in child_lines:
                bq_lines.append(f"{pad}> {line}")
            return "\n".join(bq_lines)

        elif btype == "image":
            url = props.get("url", "")
            cap_raw = props.get("caption", [])
            caption = (DocsClient._render_inline(cap_raw)
                       if isinstance(cap_raw, list) else str(cap_raw or ""))
            if url:
                return f"{pad}![{caption}]({url}){children_str}"
            return f"{pad}[image{': ' + caption if caption else ''}]{children_str}"

        elif btype == "table":
            # content est un dict {"type": "tableContent", "rows": [...]}
            # et non une liste comme pour les autres blocs.
            table_content = content if isinstance(content, dict) else {}
            rows = table_content.get("rows", [])
            if not rows:
                return ""

            # Détecte les cellules fusionnées (rowspan ou colspan > 1)
            has_merge = any(
                (cell.get("props", {}).get("rowspan", 1) or 1) > 1
                or (cell.get("props", {}).get("colspan", 1) or 1) > 1
                for row in rows
                for cell in (row.get("cells", []) if isinstance(row, dict) else [])
                if isinstance(cell, dict)
            )

            if has_merge:
                # Rendu HTML pour préserver les fusions de cellules
                # (le Markdown pipe table ne supporte pas rowspan/colspan)
                html_rows = []
                for row in rows:
                    cells = row.get("cells", []) if isinstance(row, dict) else []
                    td_parts = []
                    for cell in cells:
                        if not isinstance(cell, dict):
                            continue
                        cell_html = DocsClient._render_inline_html(cell.get("content", []))
                        props = cell.get("props", {})
                        colspan = props.get("colspan", 1) or 1
                        rowspan = props.get("rowspan", 1) or 1
                        attrs = ""
                        if colspan > 1:
                            attrs += f' colspan="{colspan}"'
                        if rowspan > 1:
                            attrs += f' rowspan="{rowspan}"'
                        _style = "border: 1px solid #ccc; padding: 6px;"
                        td_parts.append(f'<td{attrs} style="{_style}">{cell_html}</td>')
                    html_rows.append("  <tr>" + "".join(td_parts) + "</tr>")
                _table_style = "border-collapse: collapse; border: 1px solid #ccc;"
                return f'<table style="{_table_style}">\n' + "\n".join(html_rows) + "\n</table>"

            else:
                # Rendu Markdown standard (tableau sans fusion)
                rendered_rows = []
                for row in rows:
                    cells = row.get("cells", []) if isinstance(row, dict) else []
                    cell_texts = [
                        DocsClient._render_inline(cell.get("content", []) if isinstance(cell, dict) else [])
                        for cell in cells
                    ]
                    rendered_rows.append("| " + " | ".join(cell_texts) + " |")
                n_cols = max(r.count("|") - 1 for r in rendered_rows)
                separator = "| " + " | ".join(["---"] * max(n_cols, 1)) + " |"
                return "\n".join([rendered_rows[0], separator] + rendered_rows[1:])

        else:
            # paragraph ou bloc custom inconnu — extraction best-effort
            return f"{pad}{inline}{children_str}" if (inline or children_str) else ""

    @staticmethod
    def blocknote_to_markdown(blocks: list[dict]) -> str:
        """Convertit une liste de blocs BlockNote JSON en markdown standard.

        Gère les blocs natifs BlockNote (heading, paragraph, bulletListItem,
        numberedListItem, checkListItem, codeBlock, image, table) et les blocs
        custom de Docs (callout → blockquote avec émoji).
        Les blocs et inline contents inconnus ont leur texte extrait en best-effort.

        Args:
            blocks: liste de blocs BlockNote (retournée par get_json_blocks())

        Returns:
            str: contenu markdown
        """
        if not blocks:
            return ""
        rendered = [DocsClient._render_block(b) for b in blocks]
        result = "\n\n".join(r for r in rendered if r)
        return re.sub(r"\n{3,}", "\n\n", result).strip()

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
            "content_markdown": content_data.get("content") or "",
            "created_at": metadata.get("created_at"),
            "updated_at": metadata.get("updated_at"),
        }

    def fetch_children_with_content(self, parent_url_or_id,
                                    content_format: str = "markdown"):
        """
        Récupère tous les enfants d'un doc parent avec leur contenu.

        Args:
            parent_url_or_id: URL ou UUID du document parent
            content_format: format de récupération du contenu —
                'json'     : JSON BlockNote → markdown (recommandé, préserve les callouts)
                'markdown' : markdown brut depuis le Y-Provider
                'html'     : HTML converti en texte

        Returns:
            list de dicts avec id, title, content_markdown, content_format, ...
        """
        parent_id = self.extract_doc_id(parent_url_or_id)
        if not parent_id:
            raise ValueError(f"Impossible d'extraire un UUID depuis : {parent_url_or_id}")

        children = self.get_all_children(parent_id)
        results = []
        for child in children:
            child_id = child["id"]
            try:
                if content_format == "json":
                    blocks = self.get_json_blocks(child_id)
                    content_md = self.embed_internal_images(self.blocknote_to_markdown(blocks))
                    fmt = "json→md"
                elif content_format == "html":
                    html = self.get_html(child_id)
                    content_md = self.html_to_text(html)
                    fmt = "html"
                else:  # "markdown" ou "auto"
                    content_data = self.get_content(child_id, "markdown")
                    # `or ""` gère le cas {"content": null} (document jamais édité)
                    content_md = content_data.get("content") or ""
                    fmt = "markdown"
                results.append({
                    "id": child_id,
                    "title": child.get("title", ""),
                    "content_markdown": content_md,
                    "content_format": fmt,
                    "created_at": child.get("created_at"),
                    "updated_at": child.get("updated_at"),
                })
            except Exception as e:  # noqa: BLE001
                # HTTPError (400/500 Y-Provider), ConnectionError, etc.
                print(f"⚠️  Erreur pour {child_id} ({child.get('title')}): {e}")
                results.append({
                    "id": child_id,
                    "title": child.get("title", ""),
                    "content_markdown": None,  # None = signal pour re-fetch dans flatten_tree
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
                     parent_numero: str | None = None, position: int = 1,
                     is_root: bool = False,
                     content_format: str = "json") -> list[dict]:
        """
        Parcourt récursivement le tree retourné par get_tree() et retourne
        une liste de records prêts à être insérés dans Grist.

        Champs remplis : titre, emoji, titre_propre, niveau, ordre, numero,
                         url, contenu, contenu_format.
        Champs non remplis (à compléter manuellement) :
            document, parent_chapitre, mots_cles, themes.

        Args:
            node: nœud du tree (dict avec id, title, depth, path, children…)
            base_url: URL de base de l'instance Docs (ex: https://docs.numerique.gouv.fr)
            parent_numero: numéro hiérarchique du parent (ex: "1.3"), None pour la racine
            position: position du nœud parmi ses frères (1-indexé)
            is_root: si True, le nœud racine est ignoré et ses enfants sont
                     numérotés à partir de 1 directement (Guide=1, Outils=2, etc.)
            content_format: format de récupération du contenu —
                'json'     : JSON BlockNote → markdown (défaut, préserve callouts et blocs custom)
                'markdown' : texte markdown brut (peut échouer sur certains blocs custom)
                'html'     : HTML converti en texte → meilleure compatibilité émojis
                'auto'     : essaie markdown, bascule sur HTML si échec

        Returns:
            list de dicts {"fields": {...}} pour l'API Grist
        """
        records = []

        doc_id = node.get("id", "")
        titre = self._strip_emojis(node.get("title", ""))
        niveau = node.get("depth", 1)
        path = node.get("path", "")

        # Extraction de l'émoji de tête du titre (logique identique au frontend)
        emoji, titre_propre = self.extract_emoji_from_title(titre)

        children = node.get("children", [])
        numchild = node.get("numchild", 0)

        # Le tree ne retourne pas toujours tous les enfants (children: [] malgré numchild > 0).
        # On les récupère via fetch_children_with_content qui remonte aussi le contenu,
        # évitant ainsi un appel get_markdown() supplémentaire par enfant.
        if numchild > 0 and not children:
            try:
                raw = self.fetch_children_with_content(doc_id, content_format=content_format)
                children = [
                    {
                        "id": c["id"],
                        "title": c.get("title", ""),
                        "depth": niveau + 1,
                        "path": "",
                        "numchild": 0,   # sera récupéré récursivement si besoin
                        "children": [],
                        # `or ""` : content_markdown peut être None si
                        # fetch_children_with_content a capturé une erreur
                        "_content": c.get("content_markdown") or "",
                        "_content_format": (c.get("content_format", "markdown")
                                            if not c.get("error") else "conversion_echec"),
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
                                      parent_numero=None, position=i,
                                      content_format=content_format)
                )
            return records

        ordre = self._path_to_ordre(path)
        numero = f"{parent_numero}.{position}" if parent_numero else str(position)
        url = f"{base_url.rstrip('/')}/docs/{doc_id}/"

        emoji_indicator = f" {emoji}" if emoji else ""
        print(f"  {'  ' * (niveau - 2)}[{numero}]{emoji_indicator} {titre_propre}")

        # ── Récupération du contenu ──────────────────────────────────────────
        # Le contenu peut avoir été pré-chargé par le parent
        contenu = node.get("_content")
        fmt_utilise = node.get("_content_format", "markdown")

        if contenu is None:
            if content_format == "json":
                try:
                    blocks = self.get_json_blocks(doc_id)
                    contenu = self.embed_internal_images(self.blocknote_to_markdown(blocks))
                    fmt_utilise = "json→md"
                except Exception as e:
                    print(f"    ⚠️  Contenu JSON non récupéré pour {doc_id}: {e}")
                    contenu = ""
                    fmt_utilise = "erreur"

            elif content_format == "markdown":
                try:
                    contenu = self.get_markdown(doc_id)
                    fmt_utilise = "markdown"
                except Exception as e:
                    print(f"    ⚠️  Contenu non récupéré pour {doc_id}: {e}")
                    contenu = ""
                    fmt_utilise = "erreur"

            elif content_format == "html":
                try:
                    html = self.get_html(doc_id)
                    contenu = self.html_to_text(html)
                    fmt_utilise = "html"
                except Exception as e:
                    print(f"    ⚠️  Contenu HTML non récupéré pour {doc_id}: {e}")
                    contenu = ""
                    fmt_utilise = "erreur"

            else:  # "auto" : markdown puis HTML en fallback
                contenu, fmt_utilise = self.get_markdown_with_emoji_fallback(doc_id)

        # ⚠️  Ne pas appliquer strip_code_blocks ici : les blocs custom de
        # BlockNote (callout, etc.) sont sérialisés en fenced blocks dans le
        # markdown. Les supprimer ferait perdre du contenu légitime.
        # La sanitisation WAF doit être appliquée uniquement au moment de
        # l'envoi vers des API externes (Grist, etc.).

        n_emojis = self.count_emojis(contenu)
        if n_emojis:
            print(f"    ✓ {n_emojis} émoji(s) dans le contenu [{fmt_utilise}]")

        records.append({
            "fields": {
                "titre": titre,
                "emoji": emoji or "",
                "titre_propre": titre_propre,
                "niveau": niveau - 1,
                "ordre": ordre,
                "numero": numero,
                "url": url,
                "contenu": contenu,
                "contenu_format": fmt_utilise,
            }
        })

        for i, child in enumerate(children, start=1):
            records.extend(
                self.flatten_tree(child, base_url,
                                  parent_numero=numero, position=i,
                                  content_format=content_format)
            )

        return records