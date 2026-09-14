from pathlib import Path
from urllib.parse import quote

import requests

CHARACTER_BASE_URL = (
    "https://arknights.timo.beer/"
    "arkdata/assets/avg/characters"
)

CHARACTERS_DIR = (
    Path("assets")
    / "scene_images"
    / "characters"
)


def parse_character_asset_name(
    raw_name: str
) -> tuple[str, int, int]:
    raw_name = raw_name.strip()

    if "#" not in raw_name or "$" not in raw_name:
        return (
            raw_name,
            1,
            1
        )

    base_name, variant_part = raw_name.split(
        "#",
        1
    )

    expression, subvariant = variant_part.split(
        "$",
        1
    )

    return (
        base_name,
        int(expression),
        int(subvariant)
    )


def build_character_filename(
    base_name: str,
    expression: int = 1,
    subvariant: int = 1
) -> str:
    return (
        f"{base_name}"
        f"#{expression}"
        f"${subvariant}.png"
    )


def get_scene_character_image(
    base_name: str
) -> Path:
    CHARACTERS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    normalized_base_name = base_name.lower()

    filename = build_character_filename(
        base_name=normalized_base_name,
        expression=1,
        subvariant=1
    )

    local_filename = (
        f"{normalized_base_name}__1_1.png"
    )

    destination = (
        CHARACTERS_DIR
        / local_filename
    )

    if destination.exists():
        return destination

    encoded_filename = quote(
        filename,
        safe=""
    )

    url = (
        f"{CHARACTER_BASE_URL}/"
        f"{encoded_filename}"
    )

    response = requests.get(
        url,
        timeout=30
    )
    response.raise_for_status()

    destination.write_bytes(
        response.content
    )

    return destination