from PySide6.QtCore import QObject, Signal, Slot

from app.runner import (load_available_groups, load_available_operators,
                        run_translation)


class TranslationWorker(QObject):

    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    progress = Signal(int)

    def __init__(
        self,
        groups: dict,
        operators: dict,
        translation_model: str,
        context_model: str,
        regenerate_context: bool,
        ignore_translation_cache: bool,
        download_only: bool,
        generate_epub: bool,
        generate_html: bool,
        send_to_kindle: bool
    ):
        super().__init__()

        self.groups = groups
        self.operators = operators
        self.translation_model = translation_model
        self.context_model = context_model
        self.regenerate_context = regenerate_context
        self.ignore_translation_cache = (
            ignore_translation_cache
        )
        self.download_only = download_only
        self.generate_epub = generate_epub
        self.generate_html = generate_html
        self.send_to_kindle = send_to_kindle

    @Slot()
    def run(self):
        try:
            self.log.emit(
                "Iniciando proceso..."
            )

            run_translation(
                groups=self.groups,
                operators=self.operators,
                translation_model=self.translation_model,
                context_model=self.context_model,
                regenerate_context=self.regenerate_context,
                ignore_translation_cache=(
                    self.ignore_translation_cache
                ),
                download_only=self.download_only,
                generate_epub=self.generate_epub,
                generate_html=self.generate_html,
                send_to_kindle=self.send_to_kindle,
                log_callback=self.log.emit,
                progress_callback=self.progress.emit,
            )

            self.log.emit(
                "Proceso completado."
            )

        except Exception as exception:
            self.error.emit(
                str(exception)
            )

        finally:
            self.finished.emit()
            
class GroupsWorker(QObject):

    loaded = Signal(dict)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    @Slot()
    def run(self):
        try:
            self.log.emit(
                "Intentando conectar con "
                "arknights.timo.beer..."
            )

            groups = load_available_groups()

            self.loaded.emit(
                groups
            )

        except Exception as exception:
            self.error.emit(
                str(exception)
            )

        finally:
            self.finished.emit()

class OperatorsWorker(QObject):

    loaded = Signal(dict)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    @Slot()
    def run(self):
        try:
            self.log.emit(
                "Cargando operadores..."
            )

            operators = (
                load_available_operators()
            )

            self.loaded.emit(
                operators
            )

        except Exception as exception:
            self.error.emit(
                str(exception)
            )

        finally:
            self.finished.emit()