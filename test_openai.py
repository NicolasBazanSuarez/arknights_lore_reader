from pathlib import Path

from translation.openai_translator import translate_html

chapter_files = list(
    Path("output").rglob(
        "000 - Prologue, Part 1 - Interlude.html"
    )
)

if not chapter_files:
    raise FileNotFoundError(
        "No se ha encontrado el primer capítulo del prólogo"
    )

source = chapter_files[0]

log(f"Traduciendo: {source}")

html_content = source.read_text(
    encoding="utf-8"
)

translated_html = translate_html(
    html_content,
    story_id="main_0"
)

destination = source.with_name(
    f"{source.stem} - ES TEST.html"
)

destination.write_text(
    translated_html,
    encoding="utf-8"
)

log(f"Traducción generada: {destination}")