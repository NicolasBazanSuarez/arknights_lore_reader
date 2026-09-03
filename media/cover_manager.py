from pathlib import Path

import requests

COVERS_URL = "https://arknights.timo.beer/covers"
COVERS_FOLDER = Path("assets/covers")


def sync_covers(groups: dict):
    # 1. Crear la carpeta covers si no existe
    COVERS_FOLDER.mkdir(exist_ok=True)

    # Portadas que deberían existir según los grupos actuales
    required_covers = {
        group["cover"]
        for group in groups.values()
        if group.get("cover")
    }

    # 2. Portadas que ya existen localmente
    existing_covers = {
        file.name
        for file in COVERS_FOLDER.iterdir()
        if file.is_file()
    }

    # 3. Comparar ambos listados
    missing_covers = required_covers - existing_covers

    # 4. Descargar las que faltan
    for cover in missing_covers:
        download_cover(cover)


def download_cover(cover: str):
    response = requests.get(
        f"{COVERS_URL}/{cover}",
        timeout=30
    )

    response.raise_for_status()

    (COVERS_FOLDER / cover).write_bytes(response.content)