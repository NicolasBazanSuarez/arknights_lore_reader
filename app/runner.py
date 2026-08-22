from pathlib import Path

from api.client import download_catalog, get_groups
from media.cover_manager import sync_covers
from models.category import CATEGORIES
from story.manager import download_stories

GROUPS_ENDPOINT = (
    "https://arknights.timo.beer/json/covers.json"
)


def filter_groups(groups: dict) -> dict:
    return {
        group_id: group
        for group_id, group in groups.items()
        if (
            group.get("category") in CATEGORIES
            and CATEGORIES[
                group["category"]
            ].enabled
        )
    }


def create_story_folders(groups: dict):
    output_folder = Path("output")

    output_folder.mkdir(
        exist_ok=True
    )

    categories = {
        group["category"]
        for group in groups.values()
    }

    for category_id in categories:
        folder_name = CATEGORIES[
            category_id
        ].folder_name

        (
            output_folder
            / folder_name
        ).mkdir(exist_ok=True)


def run_translation(
    groups: dict,
    translation_model: str,
    context_model: str,
    regenerate_context: bool = False,
    ignore_translation_cache: bool = False,
    download_only: bool = False,
    log_callback=None,
    progress_callback=None
):
    def log(message: str):
        if log_callback:
            log_callback(message)

    log(
        "Descargando lista de historias..."
    )

    log(
        "Descargando catálogo..."
    )

    catalog = download_catalog()

    log(
        f"Historias seleccionadas: "
        f"{len(groups)}"
    )

    log(
        "Sincronizando portadas..."
    )

    sync_covers(
        groups
    )

    create_story_folders(
        groups
    )

    log(
        "Procesando historias..."
    )

    download_stories(
        groups=groups,
        catalog=catalog,
        translation_model=translation_model,
        context_model=context_model,
        regenerate_context=regenerate_context,
        ignore_translation_cache=ignore_translation_cache,
        download_only=download_only,
        log_callback=log_callback,
        progress_callback=progress_callback
    )
    
def load_available_groups() -> dict:
    return get_groups(
        GROUPS_ENDPOINT
    )