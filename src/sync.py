"""Script principal de synchronisation Docs → Grist."""

import os
from dotenv import load_dotenv

from docs_client import DocsClient
from grist_client import GristClient

TABLE_CHAPITRES = "Chapitres"


# ──────────────────────────────────────────────
#  UTILITAIRES
# ──────────────────────────────────────────────

def _path_to_ordre(path: str) -> int:
    """
    Convertit le dernier segment de 7 caractères du path (base-36) en entier.
    Permet de trier les chapitres frères dans leur ordre natif Docs.
    """
    if not path:
        return 0
    return int(path[-7:], 36)


# ──────────────────────────────────────────────
#  TRAVERSÉE DU TREE
# ──────────────────────────────────────────────

def flatten_tree(node: dict, docs_client: DocsClient, base_url: str,
                 parent_numero: str = None, position: int = 1,
                 is_root: bool = False) -> list[dict]:
    """
    Parcourt récursivement le tree retourné par DocsClient.get_tree()
    et retourne une liste de records prêts à être insérés dans Grist.

    Champs remplis : titre, niveau, ordre, numero, url, contenu.
    Champs ignorés : document, parent_chapitre, mots_cles, themes.

    Args:
        node: nœud du tree (dict avec id, title, depth, path, children…)
        docs_client: instance DocsClient authentifiée
        base_url: URL de base de l'instance Docs (ex: https://docs.numerique.gouv.fr)
        parent_numero: numéro hiérarchique du parent (ex: "1.3"), None pour la racine
        position: position du nœud parmi ses frères (1-indexé)
        is_root: si True, le nœud racine est ignoré et ses enfants sont numérotés
                 à partir de 1 directement (Guide=1, Outils=2, etc.)

    Returns:
        list de dicts {"fields": {...}} pour l'API Grist
    """
    records = []

    doc_id = node.get("id", "")
    titre = node.get("title", "")
    niveau = node.get("depth", 1)
    path = node.get("path", "")

    children = node.get("children", [])
    numchild = node.get("numchild", 0)

    # Le tree ne retourne pas toujours tous les enfants (children: [] malgré numchild > 0)
    # Dans ce cas, on les récupère explicitement via l'endpoint /children/
    if numchild > 0 and not children:
        try:
            raw_children = docs_client.get_all_children(doc_id)
            children = [
                {
                    "id": c["id"],
                    "title": c.get("title", ""),
                    "depth": niveau + 1,
                    "path": c.get("path", ""),
                    "numchild": c.get("numchild", 0),
                    "children": [],
                }
                for c in raw_children
            ]
        except Exception as e:
            print(f"  ⚠️  Impossible de récupérer les enfants de {doc_id} ({titre}): {e}")

    # Le nœud racine n'est pas numéroté : on traite ses enfants directement
    if is_root:
        print(f"[racine] {titre}")
        for i, child in enumerate(children, start=1):
            records.extend(
                flatten_tree(child, docs_client, base_url,
                             parent_numero=None, position=i)
            )
        return records

    ordre = _path_to_ordre(path)
    numero = f"{parent_numero}.{position}" if parent_numero else str(position)
    url = f"{base_url.rstrip('/')}/docs/{doc_id}/"

    print(f"  {'  ' * (niveau - 2)}[{numero}] {titre}")

    try:
        contenu = docs_client.get_markdown(doc_id)
    except Exception as e:
        print(f"  ⚠️  Contenu non récupéré pour {doc_id} ({titre}): {e}")
        contenu = ""

    records.append({
        "fields": {
            "titre": titre,
            "niveau": niveau - 1,  # On décale : les enfants directs de la racine deviennent niveau 1
            "ordre": ordre,
            "numero": numero,
            "url": url,
            "contenu": contenu,
        }
    })

    for i, child in enumerate(children, start=1):
        records.extend(
            flatten_tree(child, docs_client, base_url,
                         parent_numero=numero, position=i)
        )

    return records


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
    # On extrait juste l'origine (schema + host) pour construire les URLs de page
    from urllib.parse import urlparse
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
    records = flatten_tree(tree, docs, docs_base, is_root=True)
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
