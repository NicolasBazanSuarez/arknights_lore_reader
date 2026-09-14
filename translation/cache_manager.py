import json
from pathlib import Path

CACHE_FOLDER = Path("translation/cache")


def load_chapter_translation(
    story_id: str,
    chapter_index: int
) -> dict | None:

    path = (
        CACHE_FOLDER
        / story_id
        / f"{chapter_index:03d}.json"
    )

    if not path.exists():
        return None

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def save_chapter_translation(
    story_id: str,
    chapter_index: int,
    title: str,
    scenes: list[dict]
):
    folder = CACHE_FOLDER / story_id

    folder.mkdir(
        parents=True,
        exist_ok=True
    )

    path = folder / f"{chapter_index:03d}.json"

    data = {
        "title": title,
        "scenes": scenes
    }

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

OPERATOR_CACHE_FOLDER = (
    CACHE_FOLDER
    / "operators"
)


def load_operator_translation(
    operator_id: str
) -> dict | None:
    path = (
        OPERATOR_CACHE_FOLDER
        / f"{operator_id}.json"
    )

    if not path.exists():
        return None

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def save_operator_translation(
    operator_id: str,
    operator_data: dict
):
    OPERATOR_CACHE_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        OPERATOR_CACHE_FOLDER
        / f"{operator_id}.json"
    )

    path.write_text(
        json.dumps(
            operator_data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )
