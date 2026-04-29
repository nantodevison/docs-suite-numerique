"""Client API pour Grist."""

import os
import requests


class GristClient:
    """Client HTTP pour l'API Grist."""

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
