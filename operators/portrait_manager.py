from pathlib import Path

import requests

PORTRAIT_BASE_URL = (
    "https://arknights.timo.beer/"
    "arkdata/assets/torappu/dynamicassets/arts/charportraits"
)


def download_operator_portrait(
    operator_id: str,
    portraits_dir: Path
) -> Path | None:
    portraits_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = f"{operator_id}_1.png"
    destination = portraits_dir / filename

    if destination.exists():
        return destination

    url = f"{PORTRAIT_BASE_URL}/{filename}"

    try:
        response = requests.get(
            url,
            timeout=30
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    destination.write_bytes(
        response.content
    )

    return destination