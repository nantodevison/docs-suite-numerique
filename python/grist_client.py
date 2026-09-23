"""Client API pour Grist."""

import os
import requests


class GristClient:
    """Client HTTP pour l'API Grist."""

    # Taille maximale du champ texte libre (caractères) avant troncature.
    # Peut être surchargé à l'instance : grist._max_contenu = 50_000
    _MAX_CONTENU: int = 100_000

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        doc_id: str | None = None,
    ):
        self.api_url = (api_url or os.environ.get("GRIST_API_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("GRIST_API_KEY", "")
        self.doc_id = doc_id or os.environ.get("GRIST_DOC_ID", "")
        if not self.api_url:
            raise ValueError("GRIST_API_URL est requis.")
        if not self.api_key:
            raise ValueError("GRIST_API_KEY est requis.")
        if not self.doc_id:
            raise ValueError("GRIST_DOC_ID est requis.")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Origin": "https://grist.numerique.gouv.fr",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        })

    # ──────────────────────────────────────────────
    #  PRÉPARATION D'UN RECORD AVANT ENVOI
    # ──────────────────────────────────────────────

    def _filter_record(
        self,
        record: dict,
        columns: set[str] | None = None,
        content_field: str = "contenu",
    ) -> dict:
        """Prépare un record pour l'envoi vers Grist.

        - Filtre les champs selon `columns` (None = tous les champs)
        - Tronque le champ `content_field` si sa longueur dépasse _MAX_CONTENU

        Args:
            record:        dict au format {"fields": {...}}
            columns:       ensemble de noms de colonnes à conserver, ou None
            content_field: nom du champ texte à tronquer si besoin

        Returns:
            dict au format {"fields": {...}} prêt pour add_records()
        """
        fields = {
            k: v for k, v in record["fields"].items()
            if columns is None or k in columns
        }
        if content_field in fields and isinstance(fields[content_field], str):
            if len(fields[content_field]) > self._MAX_CONTENU:
                fields[content_field] = (
                    fields[content_field][:self._MAX_CONTENU]
                    + "\n[…contenu tronqué]"
                )
        return {"fields": fields}

    # ──────────────────────────────────────────────
    #  ENVOI EN MASSE (avec log par record)
    # ──────────────────────────────────────────────

    def send_records(
        self,
        table_id: str,
        records: list[dict],
        columns: set[str] | None = None,
        content_field: str = "contenu",
    ) -> tuple[list[int], list[dict]]:
        """Envoie une liste de records dans une table Grist, un par un.

        Filtre et tronque chaque record via _filter_record(), puis tente
        l'insertion. Trace le résultat (✓ / ✗) pour chaque record.

        Args:
            table_id:      nom de la table cible (ex : 'Chapitres')
            records:       liste de dicts {"fields": {...}}
            columns:       colonnes à conserver (None = toutes)
            content_field: champ à tronquer si trop long

        Returns:
            tuple (ok, ko) :
                ok  — liste des indices (base 1) des records envoyés avec succès
                ko  — liste de dicts décrivant chaque échec :
                      {index, titre, erreur, body, record}
        """
        ok: list[int] = []
        ko: list[dict] = []
        total = len(records)

        for i, record in enumerate(records, start=1):
            titre = (
                record["fields"].get("titre")
                or record["fields"].get("titre_propre", "?")
            )
            filtered = self._filter_record(record, columns=columns,
                                           content_field=content_field)
            contenu_len = len(filtered["fields"].get(content_field, ""))

            try:
                self.add_records(table_id, [filtered])
                ok.append(i)
                print(f"  [{i:>3}/{total}] ✓  {titre}  ({contenu_len} car.)")

            except requests.HTTPError as exc:
                body = (exc.response.text
                        if exc.response is not None else "(pas de réponse)")
                ko.append({"index": i, "titre": titre,
                           "erreur": str(exc), "body": body, "record": record})
                print(f"  [{i:>3}/{total}] ✗  {titre}  ({contenu_len} car.)")
                print(f"          → {exc}")
                print(f"          Corps Grist : {body[:300]}")

            except Exception as exc:  # noqa: BLE001
                ko.append({"index": i, "titre": titre,
                           "erreur": str(exc), "body": "", "record": record})
                print(f"  [{i:>3}/{total}] ✗  {titre}")
                print(f"          → {exc}")

        print(f"\n── Résumé ──────────────────────────────────────────")
        print(f"  Succès : {len(ok)}")
        print(f"  Échecs : {len(ko)}")
        if ko:
            print("\n  Détail des échecs :")
            for item in ko:
                print(f"    [{item['index']}] {item['titre']!r} → {item['erreur']}")
                if item.get("body"):
                    print(f"             Corps : {item['body'][:200]}")

        return ok, ko


    def get_records(self, table_id: str) -> list[dict]:
        """Retourne tous les enregistrements d'une table Grist."""
        url = f"{self.api_url}/docs/{self.doc_id}/tables/{table_id}/records"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("records", [])

    def add_records(self, table_id: str, records: list[dict], delay: float = 3.0) -> dict:
        """Envoie les records un par un avec délai, retourne les ids et liste les échecs."""
        import time
        url = f"{self.api_url}/docs/{self.doc_id}/tables/{table_id}/records"
        all_ids = []
        failures = []
        for i, record in enumerate(records):
            response = self.session.post(url, json={"records": [record]})
            if response.status_code == 200:
                all_ids.extend(response.json().get("records", []))
                print(f"  [{i:02d}] {record['fields'].get('titre','?')[:40]:40s} → OK")
            else:
                failures.append((i, record, response.status_code))
                print(f"  [{i:02d}] {record['fields'].get('titre','?')[:40]:40s} → ERREUR {response.status_code}")
            time.sleep(delay)
        if failures:
            print(f"\n{len(failures)} échec(s) sur {len(records)} records.")
            print("Accès via : grist.last_failures")
        self.last_failures = failures
        return {"records": all_ids}
        return {"records": all_ids}

    def update_records(self, table_id: str, records: list[dict]) -> dict:
        """Met à jour des enregistrements existants dans une table Grist."""
        url = f"{self.api_url}/docs/{self.doc_id}/tables/{table_id}/records"
        response = self.session.patch(url, json={"records": records})
        response.raise_for_status()
        return response.json()
