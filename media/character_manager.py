from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image, ImageDraw

CHARACTER_BASE_URL = (
    "https://arknights.timo.beer/"
    "arkdata/assets/avg/characters"
)

ASSETS_DIR = Path("assets")

CHARACTERS_DIR = (
    Path("assets")
    / "scene_images"
    / "characters"
)

SPEAKER_PORTRAITS_DIR = (
    ASSETS_DIR
    / "scene_images"
    / "speaker_portraits"
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

def get_speaker_portrait(
    base_name: str,
    size: int = 192
) -> Path:
    SPEAKER_PORTRAITS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    normalized_id = (
        normalize_character_variant(
            base_name
        )
    )

    safe_name = (
        normalized_id
        .replace("#", "__")
        .replace("$", "_")
    )

    destination = (
        SPEAKER_PORTRAITS_DIR
        / f"{safe_name}_{size}.png"
    )

    if destination.exists():
        return destination

    source_image_path = (
        get_character_variant_image(
            base_name
        )
    )

    image = Image.open(
        source_image_path
    ).convert("RGBA")

    # Recorte fijo sobre las imágenes AVG 1024x1024.
    crop_size = 350
    crop_x = 312
    crop_y = 30

    cropped = image.crop(
        (
            crop_x,
            crop_y,
            crop_x + crop_size,
            crop_y + crop_size
        )
    )

    resized = cropped.resize(
        (size, size),
        Image.Resampling.LANCZOS
    )

    mask = Image.new(
        "L",
        (size, size),
        0
    )

    draw = ImageDraw.Draw(mask)

    draw.ellipse(
        (
            0,
            0,
            size - 1,
            size - 1
        ),
        fill=255
    )

    portrait = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    portrait.paste(
        resized,
        (0, 0),
        mask
    )

    portrait.save(
        destination
    )

    return destination

def normalize_character_variant(
    character_id: str
) -> str:
    character_id = (
        character_id
        .strip()
        .lower()
    )

    if "#" not in character_id:
        return (
            f"{character_id}#1$1"
        )

    if "$" not in character_id:
        return (
            f"{character_id}$1"
        )

    return character_id

def get_character_variant_image(
    character_id: str
) -> Path:
    CHARACTERS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    normalized_id = (
        normalize_character_variant(
            character_id
        )
    )

    safe_name = (
        normalized_id
        .replace("#", "__")
        .replace("$", "_")
    )

    destination = (
        CHARACTERS_DIR
        / f"{safe_name}.png"
    )

    if destination.exists():
        return destination

    filename = (
        f"{normalized_id}.png"
    )

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