import re
from pathlib import Path

import requests

from models.category import CATEGORIES
from story.compendium_generator import generate_story_compendium
from story.sanitizer import parse_story_text
from translation.cache_manager import (load_chapter_translation,
                                       save_chapter_translation)
from translation.context_builder import (build_story_context,
                                         story_context_exists)
from translation.openai_translator import translate_chapter

STORY_BASE_URL = (
    "https://arknights.timo.beer/"
    "ArknightsGameData_Assets/en/gamedata/story"
)

def sanitize_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()

def get_chapter_title(
    index: int,
    chapter: dict
) -> str:

    story_code = chapter.get(
        "storyCode",
        ""
    ).strip()

    story_name = chapter.get(
        "storyName",
        ""
    ).strip()

    avg_tag = chapter.get(
        "avgTag",
        ""
    ).strip()

    parts = [
        f"{index:03d}"
    ]

    if story_code:
        parts.append(story_code)

    elif story_name:
        parts.append(story_name)

    if avg_tag:
        parts.append(avg_tag)

    return sanitize_name(
        " - ".join(parts)
    )

def download_chapter_source(
    story_txt: str
) -> list[dict]:

    url = f"{STORY_BASE_URL}/{story_txt}.txt"

    response = requests.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    text = response.content.decode("utf-8")

    return parse_story_text(text)

def download_stories(
    groups: dict,
    catalog: dict
):
    review = catalog.get(
        "review",
        {}
    )

    for group_id, group in groups.items():

        story_group = review.get(
            group_id
        )

        if not story_group:
            continue

        chapters = story_group.get(
            "infoUnlockDatas",
            []
        )

        if not chapters:
            continue

        chapters = sorted(
            chapters,
            key=lambda chapter: chapter.get(
                "storySort",
                0
            )
        )

        category_folder = CATEGORIES[
            group["category"]
        ].folder_name

        story_display_title = group.get(
            "title",
            group_id
        )

        story_folder = (
            Path("output")
            / category_folder
            / sanitize_name(
                story_display_title
            )
        )

        story_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        chapter_data = []

        for index, chapter in enumerate(
            chapters
        ):
            chapter_data.append({
                "index": index,

                "chapter": chapter,

                "title": get_chapter_title(
                    index,
                    chapter
                ),

                "scenes": None,

                "translation": (
                    load_chapter_translation(
                        group_id,
                        index
                    )
                )
            })

        context_exists = (
            story_context_exists(
                group_id
            )
        )

        # Para generar el contexto necesitamos
        # ver toda la historia inglesa.
        if not context_exists:

            print(
                f"Descargando fuentes para contexto: "
                f"{story_display_title}"
            )

            for item in chapter_data:

                story_txt = item[
                    "chapter"
                ].get("storyTxt")

                if not story_txt:
                    continue

                item["scenes"] = (
                    download_chapter_source(
                        story_txt
                    )
                )

            build_story_context(
                story_id=group_id,
                story_title=story_display_title,
                chapters=chapter_data
            )

        translated_chapters = []

        for item in chapter_data:

            cached_translation = item[
                "translation"
            ]

            # Ya fue traducido anteriormente.
            if cached_translation:
                print(
                    f"Usando caché: "
                    f"{item['title']}"
                )

                translated_chapters.append(
                    cached_translation
                )

                continue

            # Si no descargamos antes el TXT
            # para generar el contexto, lo hacemos ahora.
            if item["scenes"] is None:

                story_txt = item[
                    "chapter"
                ].get("storyTxt")

                if not story_txt:
                    continue

                item["scenes"] = (
                    download_chapter_source(
                        story_txt
                    )
                )

            print(
                f"Traduciendo: "
                f"{item['title']}"
            )

            (
                translated_scenes,
                translated_title
            ) = translate_chapter(
                scenes=item["scenes"],
                chapter_title=item["title"],
                story_id=group_id
            )

            save_chapter_translation(
                story_id=group_id,
                chapter_index=item["index"],
                title=translated_title,
                scenes=translated_scenes
            )

            translated_chapters.append({
                "title": translated_title,
                "scenes": translated_scenes
            })

        generate_story_compendium(
            story_folder=story_folder,
            story_title=story_display_title,
            cover_name=group.get(
                "cover"
            ),
            chapters=translated_chapters
        )