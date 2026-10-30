from pathlib import Path

import requests

BACKGROUND_BASE_URL = (
    "https://arknights.timo.beer/"
    "game/en/avg/backgrounds"
)

IMAGE_BASE_URL = (
    "https://arknights.timo.beer/"
    "game/en/avg/images"
)

SCENE_IMAGES_FOLDER = Path("assets/scene_images")


def get_scene_image(image_name: str, image_type: str) -> Path:
    folder = SCENE_IMAGES_FOLDER / image_type
    folder.mkdir(parents=True, exist_ok=True)

    normalized_name = image_name.lower()

    destination = folder / f"{normalized_name}.webp"

    if destination.exists():
        return destination

    if image_type == "background":
        base_url = BACKGROUND_BASE_URL
    else:
        base_url = IMAGE_BASE_URL

    response = requests.get(
        f"{base_url}/{normalized_name}.webp",
        timeout=30
    )
    response.raise_for_status()

    destination.write_bytes(response.content)

    return destination