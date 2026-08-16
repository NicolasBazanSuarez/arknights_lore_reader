import os
import shutil
from html import escape
from pathlib import Path

from media.background_manager import get_scene_image

TEMPLATE_PATH = Path(__file__).parent / "templates" / "story.html"
STYLE_PATH = Path(__file__).parent / "styles" / "story.css"
OUTPUT_STYLE_PATH = Path("output") / "story.css"


def copy_stylesheet() -> Path:
    OUTPUT_STYLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(
        STYLE_PATH,
        OUTPUT_STYLE_PATH
    )

    return OUTPUT_STYLE_PATH


def generate_story_html(
    scenes: list[dict],
    chapter_folder: Path,
    chapter_title: str = ""
) -> str:

    scenes_html = []

    for index, scene in enumerate(scenes, start=1):
        background_name = scene["background"]

        image_html = ""

        if background_name != "UNKNOWN":
            image_file = get_scene_image(
                background_name,
                scene["image_type"]
            )

            relative_image_path = Path(
                os.path.relpath(image_file, chapter_folder)
            ).as_posix()

            image_html = (
                f'<img class="scene-image" '
                f'src="{escape(relative_image_path)}" '
                f'alt="{escape(background_name)}">'
            )

        dialogue_blocks_html = []

        for block in scene["dialogues"]:
            lines_html = "".join(
                f'<div class="line">{escape(line)}</div>'
                for line in block["lines"]
            )

            if block["speaker"]:
                dialogue_blocks_html.append(
                    f'''
                    <div class="dialogue-block">
                        <div class="speaker">
                            {escape(block["speaker"])}:
                        </div>

                        <div class="lines">
                            {lines_html}
                        </div>
                    </div>
                    '''
                )

            else:
                dialogue_blocks_html.append(
                    f'''
                    <div class="dialogue-block narrator">
                        <div class="lines">
                            {lines_html}
                        </div>
                    </div>
                    '''
                )

        scenes_html.append(
            f'''
            <section class="scene">

                <div class="scene-content">

                    <div class="scene-image-wrapper">
                        {image_html}
                    </div>

                    <div class="dialogues">
                        {"".join(dialogue_blocks_html)}
                    </div>

                </div>

            </section>
            '''
        )

    safe_title = escape(chapter_title or "Chapter")

    stylesheet = copy_stylesheet()

    relative_stylesheet_path = Path(
        os.path.relpath(stylesheet, chapter_folder)
    ).as_posix()

    template = TEMPLATE_PATH.read_text(
        encoding="utf-8"
    )

    return (
        template
        .replace("{{TITLE}}", safe_title)
        .replace("{{CSS_PATH}}", relative_stylesheet_path)
        .replace("{{SCENES}}", "".join(scenes_html))
    )