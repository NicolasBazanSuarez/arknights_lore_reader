import os
from html import escape
from pathlib import Path

from media.background_manager import get_scene_image

TOP_SECTIONS_ORDER = [
    "Basic Info",
    "Physical Exam",
    "Profile",
    "Clinical Analysis"
]


def _format_text(
    text: str
) -> str:
    return "<br>".join(
        escape(line)
        for line in text.splitlines()
    )


def _section_title(
    section
) -> str:
    if isinstance(section, dict):
        return section.get(
            "title",
            ""
        )
    return section[0]


def _section_content(
    section
) -> str:
    if isinstance(section, dict):
        return section.get(
            "text",
            ""
        )
    return section[1]

def render_info_card(
    section,
    css_class: str
) -> str:
    title = _section_title(
        section
    )

    content = _section_content(
        section
    )

    return f"""
    <section class="{css_class}">
        <h2 class="info-section-title">
            {escape(title)}
        </h2>

        <p class="info-section-content">
            {_format_text(content)}
        </p>
    </section>
    """


def split_operator_sections(
    file_sections: list
) -> tuple[dict, list]:

    top_sections = {}
    extra_sections = []

    for section in file_sections:
        title = _section_title(
            section
        )

        if title in TOP_SECTIONS_ORDER:
            top_sections[title] = section
        else:
            extra_sections.append(
                section
            )

    return (
        top_sections,
        extra_sections
    )


def render_top_sections(
    sections: dict
) -> str:

    basic_info = sections.get(
        "Basic Info"
    )

    physical_exam = sections.get(
        "Physical Exam"
    )

    profile = sections.get(
        "Profile"
    )

    clinical_analysis = sections.get(
        "Clinical Analysis"
    )

    parts = [
        '<div class="operator-info-layout">'
    ]

    if basic_info or physical_exam:
        parts.append(
            '<div class="operator-two-columns">'
        )

        if basic_info:
            parts.append(
                render_info_card(
                    basic_info,
                    "info-section"
                )
            )

        if physical_exam:
            parts.append(
                render_info_card(
                    physical_exam,
                    "info-section"
                )
            )

        parts.append("</div>")

    if profile:
        parts.append(
            render_info_card(
                profile,
                "info-section full-width"
            )
        )

    if clinical_analysis:
        parts.append(
            render_info_card(
                clinical_analysis,
                "info-section full-width"
            )
        )

    parts.append("</div>")

    return "".join(parts)


def render_archive_sections(
    sections: list
) -> str:
    if not sections:
        return ""

    columns = len(sections)

    return (
        f'<section class="archive-grid" '
        f'style="grid-template-columns: repeat({columns}, 1fr);">'
        + "".join(
            render_info_card(
                section,
                "archive-section"
            )
            for section in sections
        )
        + "</section>"
    )


def render_modules(
    modules: list
) -> str:
    if not modules:
        return ""

    parts = [
        """
        <div class="page-break"></div>
        <section>
            <h1 class="modules-title">Módulos</h1>
        """
    ]

    for module in modules:
        name = module.get(
            "name",
            module.get(
                "id",
                "Módulo"
            )
        )

        description = module.get(
            "description",
            module.get(
                "uniEquipDesc",
                ""
            )
        )

        parts.append(
            f"""
            <article class="module-card">
                <h2 class="module-title">{escape(name)}</h2>
                <p class="module-description">{_format_text(description)}</p>
            </article>
            """
        )

    parts.append(
        "</section>"
    )

    return "".join(parts)


def render_story_scenes(
    scenes: list[dict],
    operator_folder: Path
) -> str:

    scenes_html = []

    for scene in scenes:
        background_name = scene.get(
            "background",
            "UNKNOWN"
        )

        image_html = ""

        if background_name != "UNKNOWN":

            image_file = get_scene_image(
                background_name,
                scene.get(
                    "image_type",
                    "background"
                )
            )

            relative_image_path = Path(
                os.path.relpath(
                    image_file,
                    operator_folder
                )
            ).as_posix()

            image_html = (
                f'<img class="scene-image" '
                f'src="{escape(relative_image_path)}" '
                f'alt="{escape(background_name)}">'
            )

        dialogue_blocks_html = []

        for block in scene.get(
            "dialogues",
            []
        ):

            lines_html = "".join(
                f'<div class="dialogue-line">{escape(line)}</div>'
                for line in block.get(
                    "lines",
                    []
                )
            )

            speaker = block.get(
                "speaker",
                ""
            ).strip()

            if speaker:
                dialogue_blocks_html.append(
                    f'''
                    <div class="dialogue-block">
                        <div class="dialogue-speaker">
                            {escape(speaker)}:
                        </div>

                        <div class="dialogue-lines">
                            {lines_html}
                        </div>
                    </div>
                    '''
                )
            else:
                dialogue_blocks_html.append(
                    f'''
                    <div class="dialogue-block narrator">
                        <div class="dialogue-lines">
                            {lines_html}
                        </div>
                    </div>
                    '''
                )

        scenes_html.append(
            f'''
            <section class="story-scene">
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

    return "".join(
        scenes_html
    )


def render_stories(
    stories: list,
    operator_folder: Path
) -> str:
    if not stories:
        return ""

    parts = [
        """
        <div class="page-break"></div>
        <section class="operator-stories">
        """
    ]

    for story in stories:
        story_name = story.get(
            "name",
            story.get(
                "id",
                "Historia"
            )
        )

        parts.append(
            f"""
            <article class="operator-record">
                <h2 class="record-title">
                    {escape(story_name)}
                </h2>
            """
        )

        chapters = story.get(
            "chapters",
            []
        )

        for chapter in chapters:
            chapter_name = chapter.get(
                "name",
                "Capítulo"
            )

            show_chapter_title = not (
                len(chapters) == 1
                and chapter_name == story_name
            )

            chapter_title_html = ""

            if show_chapter_title:
                chapter_title_html = f"""
                <h3 class="chapter-title">
                    {escape(chapter_name)}
                </h3>
                """

            parts.append(
                f"""
                <section class="operator-record-chapter">
                    {chapter_title_html}

                    {render_story_scenes(
                        chapter.get(
                            "scenes",
                            []
                        ),
                        operator_folder
                    )}
                </section>
                """
            )

        parts.append(
            "</article>"
        )

    parts.append(
        "</section>"
    )

    return "".join(parts)


def generate_operator_html(
    operator_data: dict,
    operator_folder: Path,
    portrait_path: Path | None
) -> str:
    css_path = Path(__file__).with_name(
        "operator.css"
    )
    css_content = css_path.read_text(
        encoding="utf-8"
    )

    top_sections, archive_sections = split_operator_sections(
        operator_data.get(
            "files",
            []
        )
    )

    portrait_html = ""

    if portrait_path is not None:
        portrait_rel = os.path.relpath(
            portrait_path,
            operator_folder
        ).replace(
            "\\",
            "/"
        )

        portrait_html = f"""
        <div class="operator-portrait-column">
            <img
                class="operator-portrait"
                src="{escape(portrait_rel)}"
                alt="{escape(operator_data.get('name', 'Operator'))}"
            >
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <title>{escape(operator_data.get("name", "Operator"))}</title>
        <style>
        {css_content}
        </style>
    </head>
    <body>
        <div class="document">
            <h1 class="operator-title">
                {escape(operator_data.get("name", "Operator"))}
            </h1>

            <section class="operator-summary">
                {portrait_html}

                <div class="operator-info-column">
                    {render_top_sections(top_sections)}
                </div>
            </section>

            <section class="operator-archives">
                {render_archive_sections(archive_sections)}
            </section>

            {render_modules(operator_data.get("modules", []))}
            {render_stories(
                operator_data.get("stories", []),
                operator_folder
            )}
        </div>
    </body>
    </html>
    """