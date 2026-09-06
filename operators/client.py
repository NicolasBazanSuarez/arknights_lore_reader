import requests

FILES_URL = (
    "https://arknights.timo.beer/"
    "json/files.en.json"
)

MODULES_URL = (
    "https://arknights.timo.beer/"
    "json/modules.en.json"
)


def download_operator_files() -> dict:
    response = requests.get(
        FILES_URL,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def download_modules() -> dict:
    response = requests.get(
        MODULES_URL,
        timeout=30
    )

    response.raise_for_status()

    return response.json()