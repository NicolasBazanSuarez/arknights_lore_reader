from pathlib import Path

from api.client import download_catalog, get_groups
from media.cover_manager import sync_covers
from models.category import CATEGORIES
from story.manager import download_stories

GROUPS_ENDPOINT = "https://arknights.timo.beer/json/covers.json"


def filter_groups(groups: dict) -> dict:
    return {
        group_id: group
        for group_id, group in groups.items()
        if (
            group.get("category") in CATEGORIES
            and CATEGORIES[group["category"]].enabled
        )
    }


def create_story_folders(groups: dict):
    output_folder = Path("output")
    output_folder.mkdir(exist_ok=True)

    categories = {
        group["category"]
        for group in groups.values()
    }

    for category_id in categories:
        folder_name = CATEGORIES[category_id].folder_name

        (output_folder / folder_name).mkdir(
            exist_ok=True
        )


def main():
    groups = get_groups(GROUPS_ENDPOINT)

    catalog = download_catalog()

    groups = filter_groups(groups)

    sync_covers(groups)

    create_story_folders(groups)

    download_stories(
        groups,
        catalog
    )


if __name__ == "__main__":
    main()