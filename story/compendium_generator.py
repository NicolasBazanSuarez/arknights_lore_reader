import os
from html import escape
from pathlib import Path

from story.html_generator import copy_stylesheet, generate_story_html

TEMPLATE_PATH = (
    Path(__file__).parent
    / "templates"
    / "compendium.html"
)

COVERS_FOLDER = Path("assets/covers")


def extract_body(html: str) -> str:
    if "<body>" not in html or "</body>" not in html:
        return ""

    return (
        html
        .split("<body>", 1)[1]
        .split("</body>", 1)[0]
        .strip()
    )


def generate_story_compendium(
    story_folder: Path,
    story_title: str,
    cover_name: str | None,
    chapters: list[dict]
):
    if not chapters:
        return

    chapters_html = []

    for chapter in chapters:
        chapter_html = generate_story_html(
            scenes=chapter["scenes"],
            chapter_folder=story_folder,
            chapter_title=chapter["title"]
        )

        chapter_body = extract_body(
            chapter_html
        )

        chapters_html.append(
            f"""
            <section class="compiled-chapter">
                {chapter_body}
            </section>
            """
        )

    cover_html = ""

    if cover_name:
        cover_path = COVERS_FOLDER / cover_name

        if cover_path.exists():
            relative_cover_path = Path(
                os.path.relpath(
                    cover_path,
                    story_folder
                )
            ).as_posix()

            cover_html = (
                f'<div class="cover-page">'
                f'<img class="cover-image" '
                f'src="{escape(relative_cover_path)}" '
                f'alt="{escape(story_title)}">'
                f'</div>'
            )

    stylesheet = copy_stylesheet()

    relative_stylesheet_path = Path(
        os.path.relpath(
            stylesheet,
            story_folder
        )
    ).as_posix()

    template = TEMPLATE_PATH.read_text(
        encoding="utf-8"
    )

    final_html = (
        template
        .replace(
            "{{TITLE}}",
            escape(story_title)
        )
        .replace(
            "{{CSS_PATH}}",
            relative_stylesheet_path
        )
        .replace(
            "{{COVER}}",
            cover_html
        )
        .replace(
            "{{CHAPTERS}}",
            "".join(chapters_html)
        )
    )

    destination = (
        story_folder
        / f"{story_title}.html"
    )

    destination.write_text(
        final_html,
        encoding="utf-8"
    )