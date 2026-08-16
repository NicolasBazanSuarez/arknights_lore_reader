from pathlib import Path

import requests

CATALOG_URL = "https://arknights.timo.beer/json/catalog.en.json"
CATALOG_PATH = Path("assets/catalog.en.json")

def get_groups(api_url: str) -> dict:
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()

    data = response.json()

    return data.get("groups", {})

def download_catalog() -> dict:
    response = requests.get(CATALOG_URL, timeout=30)
    response.raise_for_status()

    catalog = response.json()

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    CATALOG_PATH.write_text(
        response.text,
        encoding="utf-8"
    )

    return catalog