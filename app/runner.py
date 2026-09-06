from pathlib import Path

from api.client import download_catalog, get_groups
from media.cover_manager import sync_covers
from models.category import CATEGORIES
from operators.client import download_modules, download_operator_files
from operators.html_generator import generate_operator_html
from operators.manager import get_operator_data
from operators.portrait_manager import download_operator_portrait
from story.catalog_resolver import build_speaker_names
from story.manager import download_chapter_source, download_stories

OUTPUT_DIR = Path("output")
ASSETS_DIR = Path("assets")

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
    operators: dict,
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

    if groups:

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
            regenerate_context=(
                regenerate_context
            ),
            ignore_translation_cache=(
                ignore_translation_cache
            ),
            download_only=download_only,
            log_callback=log_callback,
            progress_callback=(
                progress_callback
            )
        )
        
    if operators:

        log(
            f"Operadores seleccionados: "
            f"{len(operators)}"
        )

        log(
            "Descargando archivos "
            "de operadores..."
        )

        files_data = (
            download_operator_files()
        )

        log(
            "Descargando módulos..."
        )

        modules_data = (
            download_modules()
        )
        
        speaker_names = build_speaker_names(
            catalog
        )

        log(
            "Procesando operadores..."
        )

        for operator_id, operator in (
            operators.items()
        ):

            operator_name = operator.get(
                "name",
                operator_id
            )

            log(
                f"Procesando operador: "
                f"{operator_name}"
            )

            operator_data = get_operator_data(
                operator_id=operator_id,
                operator_name=operator_name,
                catalog=catalog,
                files_data=files_data,
                modules_data=modules_data
            )

            log(
                f"  Archivos encontrados: "
                f"{len(operator_data['files'])}"
            )

            log(
                f"  Módulos encontrados: "
                f"{len(operator_data['modules'])}"
            )

            log(
                f"  Operator Records encontrados: "
                f"{len(operator_data['stories'])}"
            )

            # ---------------------------------
            # Descargar historias del operador
            # ---------------------------------

            for story in operator_data[
                "stories"
            ]:

                log(
                    f"  Operator Record: "
                    f"{story['name']}"
                )

                for chapter in story[
                    "chapters"
                ]:

                    log(
                        f"    Descargando: "
                        f"{chapter['storyTxt']}"
                    )

                    chapter["scenes"] = (
                        download_chapter_source(
                            chapter["storyTxt"],
                            speaker_names
                        )
                    )

                    log(
                        f"    Escenas encontradas: "
                        f"{len(chapter['scenes'])}"
                    )

            # ---------------------------------
            # Crear carpeta del operador
            # ---------------------------------

            operator_output_folder = (
                OUTPUT_DIR
                / "Operators"
                / operator_name
            )

            operator_output_folder.mkdir(
                parents=True,
                exist_ok=True
            )

            # ---------------------------------
            # Descargar retrato
            # ---------------------------------

            portrait_path = (
                download_operator_portrait(
                    operator_id=operator_id,
                    portraits_dir=(
                        ASSETS_DIR
                        / "operators"
                        / "portraits"
                    )
                )
            )

            # ---------------------------------
            # Generar HTML
            # ---------------------------------

            html_content = generate_operator_html(
                operator_data=operator_data,
                operator_folder=operator_output_folder,
                portrait_path=portrait_path
            )

            output_file = (
                operator_output_folder
                / f"{operator_name}.html"
            )

            output_file.write_text(
                html_content,
                encoding="utf-8"
            )

            log(
                f"  HTML generado: "
                f"{output_file}"
            )
    
def load_available_groups() -> dict:
    return get_groups(
        GROUPS_ENDPOINT
    )

def load_available_operators() -> dict:
    catalog = download_catalog()

    operators = {}

    for operator_id, data in catalog.get(
        "ops",
        {}
    ).items():

        if not isinstance(data, list):
            continue

        if not data:
            continue

        name = data[0].strip()

        if not name:
            continue

        operators[operator_id] = {
            "id": operator_id,
            "name": name
        }

    return operators