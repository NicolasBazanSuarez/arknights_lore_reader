from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (QCheckBox, QComboBox, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QMainWindow, QPlainTextEdit,
                               QProgressBar, QPushButton, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from models.category import CATEGORIES
from ui.worker import GroupsWorker, OperatorsWorker, TranslationWorker


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Arknights Translator"
        )

        self.resize(1000, 700)
        
        self.groups = {}

        self.category_checkboxes = {}

        self.story_selection = {}
        
        self.operators = {}

        self.operator_selection = {}

        self.operators_loaded = False

        self.setup_ui()
        
        self.start_button.clicked.connect(
            self.start_translation
        )
        
        self.start_button.setEnabled(
            False
        )

        self.load_groups_async()
        
    def on_category_changed(
        self,
        category_id: str,
        state: int
    ):
        if (
            category_id == "operators"
            and state
            and not self.operators_loaded
        ):
            self.load_operators_async()

        self.refresh_stories()
        
    def load_operators_async(self):

        if (
            hasattr(self, "operators_thread")
            and self.operators_thread is not None
            and self.operators_thread.isRunning()
        ):
            return

        self.log_output.appendPlainText(
            "Cargando listado de operadores..."
        )

        self.operators_thread = QThread()

        self.operators_worker = (
            OperatorsWorker()
        )

        self.operators_worker.moveToThread(
            self.operators_thread
        )

        self.operators_thread.started.connect(
            self.operators_worker.run
        )

        self.operators_worker.loaded.connect(
            self.on_operators_loaded
        )

        self.operators_worker.error.connect(
            self.on_operators_error
        )

        self.operators_worker.finished.connect(
            self.operators_thread.quit
        )

        self.operators_worker.finished.connect(
            self.operators_worker.deleteLater
        )

        self.operators_thread.finished.connect(
            self.operators_thread.deleteLater
        )

        self.operators_thread.finished.connect(
            self.on_operators_thread_finished
        )

        self.operators_thread.start()
        
    def on_operators_loaded(
        self,
        operators: dict
    ):
        self.operators = operators

        self.operators_loaded = True

        self.log_output.appendPlainText(
            f"Operadores cargados: "
            f"{len(operators)}"
        )

        self.refresh_stories()
        
    def on_operators_error(
        self,
        message: str
    ):
        self.log_output.appendPlainText(
            "No se ha podido cargar "
            "el listado de operadores."
        )

        self.log_output.appendPlainText(
            f"ERROR: {message}"
        )
        
    def on_operators_thread_finished(
        self
    ):
        self.operators_worker = None
        self.operators_thread = None
        
    def start_translation(self):
        
        selected_groups = (
            self.get_selected_groups()
        )
        
        selected_operators = (
            self.get_selected_operators()
        )

        if (
            not selected_groups
            and not selected_operators
        ):
            self.log_output.appendPlainText(
                "No hay historias ni operadores "
                "seleccionados."
            )
            return
        
        translation_model = (
            self.translation_model.currentText()
        )

        context_model = (
            self.context_model.currentText()
        )
        
        regenerate_context = (
            self.regenerate_context_checkbox.isChecked()
        )

        ignore_translation_cache = (
            self.ignore_cache_checkbox.isChecked()
        )

        download_only = (
            self.download_only_checkbox.isChecked()
        )
        
        self.start_button.setEnabled(
            False
        )

        self.progress_bar.setRange(
            0,
            100
        )

        self.progress_bar.setValue(
            0
        )

        self.log_output.appendPlainText(
            "Preparando proceso..."
        )

        # -----------------------------
        # Crear hilo
        # -----------------------------

        self.thread = QThread()

        # -----------------------------
        # Crear worker
        # -----------------------------

        self.worker = TranslationWorker(
            groups=selected_groups,
            operators=selected_operators,
            translation_model=translation_model,
            context_model=context_model,
            regenerate_context=regenerate_context,
            ignore_translation_cache=ignore_translation_cache,
            download_only=download_only
        )

        self.worker.moveToThread(
            self.thread
        )

        # -----------------------------
        # Iniciar worker
        # -----------------------------

        self.thread.started.connect(
            self.worker.run
        )

        # -----------------------------
        # Mensajes
        # -----------------------------

        self.worker.log.connect(
            self.log_output.appendPlainText
        )
        
        self.worker.progress.connect(
            self.progress_bar.setValue
        )

        self.worker.error.connect(
            self.on_translation_error
        )

        # -----------------------------
        # Finalización
        # -----------------------------

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

        self.thread.finished.connect(
            self.on_translation_finished
        )

        # -----------------------------
        # Arrancar
        # -----------------------------

        self.thread.start()

    def setup_ui(self):
        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        # ---------------------------------
        # Zona superior
        # ---------------------------------

        content_layout = QHBoxLayout()

        main_layout.addLayout(
            content_layout
        )

        # ---------------------------------
        # Categorías
        # ---------------------------------

        categories_group = QGroupBox(
            "Categorías"
        )

        categories_layout = QVBoxLayout(
            categories_group
        )
        
        for category_id, category in CATEGORIES.items():

            checkbox = QCheckBox(
                category.folder_name
            )

            checkbox.setChecked(
                category.enabled
            )
            
            checkbox.setEnabled(
                category.selectable
            )

            checkbox.stateChanged.connect(
                lambda state, cid=category_id:
                    self.on_category_changed(
                        cid,
                        state
                    )
            )

            self.category_checkboxes[
                category_id
            ] = checkbox

            categories_layout.addWidget(
                checkbox
            )

        categories_layout.addStretch()

        content_layout.addWidget(
            categories_group
        )

        # ---------------------------------
        # Historias
        # ---------------------------------

        stories_group = QGroupBox(
            "Historias"
        )

        stories_layout = QVBoxLayout(
            stories_group
        )

        # ---------------------------------
        # Buscador
        # ---------------------------------

        self.story_search = QLineEdit()

        self.story_search.setPlaceholderText(
            "Buscar..."
        )

        self.story_search.textChanged.connect(
            self.filter_stories
        )

        stories_layout.addWidget(
            self.story_search
        )

        # ---------------------------------
        # Árbol de historias
        # ---------------------------------

        self.stories_tree = QTreeWidget()

        self.stories_tree.setHeaderHidden(
            True
        )

        self.stories_tree.itemChanged.connect(
            self.on_story_item_changed
        )

        stories_layout.addWidget(
            self.stories_tree
        )

        self.toggle_all_stories_button = QPushButton(
            "Seleccionar / deseleccionar todo"
        )

        self.toggle_all_stories_button.clicked.connect(
            self.toggle_all_stories
        )

        stories_layout.addWidget(
            self.toggle_all_stories_button
        )
        
        self.retry_connection_button = QPushButton(
            "Reintentar conexión"
        )

        self.retry_connection_button.clicked.connect(
            self.load_groups_async
        )

        stories_layout.addWidget(
            self.retry_connection_button
        )

        content_layout.addWidget(
            stories_group,
            1
        )

        # ---------------------------------
        # Configuración
        # ---------------------------------

        settings_group = QGroupBox(
            "Configuración"
        )

        settings_layout = QVBoxLayout(
            settings_group
        )

        settings_layout.addWidget(
            QLabel("Modelo de traducción")
        )

        self.translation_model = QComboBox()
        
        self.translation_model.setEditable(
            True
        )

        self.translation_model.addItem(
            "gpt-5.6-luna"
        )

        settings_layout.addWidget(
            self.translation_model
        )

        settings_layout.addWidget(
            QLabel("Modelo de contexto")
        )

        self.context_model = QComboBox()
        
        self.context_model.setEditable(
            True
        )

        self.context_model.addItem(
            "gpt-5.6-terra"
        )

        settings_layout.addWidget(
            self.context_model
        )

        settings_layout.addStretch()

        content_layout.addWidget(
            settings_group
        )
        
        self.regenerate_context_checkbox = QCheckBox(
            "Regenerar contexto"
        )

        settings_layout.addWidget(
            self.regenerate_context_checkbox
        )

        self.ignore_cache_checkbox = QCheckBox(
            "Ignorar caché de traducciones"
        )

        settings_layout.addWidget(
            self.ignore_cache_checkbox
        )

        self.download_only_checkbox = QCheckBox(
            "Solo descargar (sin traducir)"
        )

        settings_layout.addWidget(
            self.download_only_checkbox
        )

        self.download_only_checkbox.stateChanged.connect(
            self.update_translation_controls
        )

        # ---------------------------------
        # Botón
        # ---------------------------------

        self.start_button = QPushButton(
            "Iniciar"
        )

        main_layout.addWidget(
            self.start_button
        )

        # ---------------------------------
        # Progreso
        # ---------------------------------

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100
        )

        self.progress_bar.setValue(
            0
        )

        self.progress_bar.setValue(0)

        main_layout.addWidget(
            self.progress_bar
        )

        # ---------------------------------
        # Log
        # ---------------------------------

        main_layout.addWidget(
            QLabel("Log")
        )

        self.log_output = QPlainTextEdit()

        self.log_output.setReadOnly(
            True
        )

        main_layout.addWidget(
            self.log_output,
            1
        )
        
    def on_translation_error(
        self,
        message: str
    ):
        self.log_output.appendPlainText(
            f"ERROR: {message}"
        )
        
    def on_translation_finished(self):
        self.progress_bar.setRange(
            0,
            100
        )

        self.progress_bar.setValue(
            100
        )

        self.start_button.setEnabled(
            True
        )

        self.worker = None
        self.thread = None
        
    def load_groups_async(self):
        
        if (
            hasattr(self, "groups_thread")
            and self.groups_thread is not None
            and self.groups_thread.isRunning()
        ):
            return

        self.start_button.setEnabled(
            False
        )
        
        self.retry_connection_button.setEnabled(
            False
        )

        self.log_output.appendPlainText(
            "Intentando conectar con "
            "arknights.timo.beer..."
        )

        self.groups_thread = QThread()

        self.groups_worker = GroupsWorker()

        self.groups_worker.moveToThread(
            self.groups_thread
        )

        self.groups_thread.started.connect(
            self.groups_worker.run
        )

        self.groups_worker.loaded.connect(
            self.on_groups_loaded
        )

        self.groups_worker.error.connect(
            self.on_groups_error
        )

        self.groups_worker.finished.connect(
            self.groups_thread.quit
        )

        self.groups_worker.finished.connect(
            self.groups_worker.deleteLater
        )

        self.groups_thread.finished.connect(
            self.groups_thread.deleteLater
        )

        self.groups_thread.finished.connect(
            self.on_groups_thread_finished
        )

        self.groups_thread.start()
            
    def refresh_stories(self):
        enabled_categories = {
            category_id
            for category_id, checkbox
            in self.category_checkboxes.items()
            if checkbox.isChecked()
        }

        self.stories_tree.blockSignals(
            True
        )

        self.stories_tree.clear()

        category_items = {}

        # Crear primero los desplegables
        # de las categorías seleccionadas.
        for category_id, category in CATEGORIES.items():

            if category_id not in enabled_categories:
                continue

            category_item = QTreeWidgetItem(
                [category.folder_name]
            )

            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(
                0,
                font
            )

            self.stories_tree.addTopLevelItem(
                category_item
            )

            category_items[
                category_id
            ] = category_item

        # Añadir cada historia dentro de
        # su categoría correspondiente.
        for group_id, group in self.groups.items():

            category_id = group.get(
                "category"
            )

            if category_id not in category_items:
                continue

            title = group.get(
                "title",
                group_id
            )

            item = QTreeWidgetItem(
                [title]
            )

            item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                group_id
            )

            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
            )

            selected = self.story_selection.get(
                group_id,
                True
            )

            item.setCheckState(
                0,
                (
                    Qt.CheckState.Checked
                    if selected
                    else Qt.CheckState.Unchecked
                )
            )

            category_items[
                category_id
            ].addChild(
                item
            )

        # ---------------------------------
        # Operators
        # ---------------------------------

        operators_category = (
            category_items.get(
                "operators"
            )
        )

        if (
            operators_category
            and self.operators_loaded
        ):

            sorted_operators = sorted(
                self.operators.items(),
                key=lambda item:
                    item[1]["name"].casefold()
            )

            for operator_id, operator in (
                sorted_operators
            ):

                item = QTreeWidgetItem(
                    [operator["name"]]
                )

                item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    operator_id
                )

                item.setData(
                    0,
                    Qt.ItemDataRole.UserRole + 1,
                    "operator"
                )

                item.setFlags(
                    item.flags()
                    | Qt.ItemFlag.ItemIsUserCheckable
                )

                selected = (
                    self.operator_selection.get(
                        operator_id,
                        False
                    )
                )

                item.setCheckState(
                    0,
                    (
                        Qt.CheckState.Checked
                        if selected
                        else Qt.CheckState.Unchecked
                    )
                )

                operators_category.addChild(
                    item
                )
                
        # Abrir inicialmente las categorías.
        for category_item in category_items.values():
            category_item.setExpanded(
                True
            )

        self.stories_tree.blockSignals(
            False
        )

        self.filter_stories(
            self.story_search.text()
        )
    
    def on_story_item_changed(
        self,
        item: QTreeWidgetItem,
        column: int
    ):
        item_id = item.data(
            0,
            Qt.ItemDataRole.UserRole
        )

        if item_id is None:
            return

        item_type = item.data(
            0,
            Qt.ItemDataRole.UserRole + 1
        )

        selected = (
            item.checkState(0)
            == Qt.CheckState.Checked
        )

        if item_type == "operator":

            self.operator_selection[
                item_id
            ] = selected

            return

        self.story_selection[
            item_id
        ] = selected
        
    def get_selected_groups(
        self
    ) -> dict:

        selected_groups = {}

        for category_index in range(
            self.stories_tree.topLevelItemCount()
        ):

            category_item = (
                self.stories_tree.topLevelItem(
                    category_index
                )
            )

            for child_index in range(
                category_item.childCount()
            ):

                item = category_item.child(
                    child_index
                )

                if (
                    item.checkState(0)
                    != Qt.CheckState.Checked
                ):
                    continue

                group_id = item.data(
                    0,
                    Qt.ItemDataRole.UserRole
                )

                if group_id in self.groups:
                    selected_groups[
                        group_id
                    ] = self.groups[
                        group_id
                    ]

        return selected_groups

    def get_selected_operators(
        self
    ) -> dict:

        return {
            operator_id: self.operators[operator_id]
            for operator_id, selected
            in self.operator_selection.items()
            if (
                selected
                and operator_id in self.operators
            )
        }
    
    def update_translation_controls(self):
        translation_enabled = (
            not self.download_only_checkbox.isChecked()
        )

        self.translation_model.setEnabled(
            translation_enabled
        )

        self.context_model.setEnabled(
            translation_enabled
        )

        self.regenerate_context_checkbox.setEnabled(
            translation_enabled
        )

        self.ignore_cache_checkbox.setEnabled(
            translation_enabled
        )
        
    def on_groups_loaded(
        self,
        groups: dict
    ):
        
        self.groups = groups

        self.refresh_stories()

        self.log_output.appendPlainText(
            f"Conexión establecida. "
            f"Historias cargadas: "
            f"{len(groups)}"
        )

        self.start_button.setEnabled(
            True
        )
        
        self.retry_connection_button.setEnabled(
            True
        )
        
    def on_groups_error(
        self,
        message: str
    ):
        self.log_output.appendPlainText(
            "No se ha podido conectar con "
            "arknights.timo.beer."
        )

        self.log_output.appendPlainText(
            f"ERROR: {message}"
        )

        self.start_button.setEnabled(
            False
        )
        
        self.retry_connection_button.setEnabled(
            True
        )
    
    def on_groups_thread_finished(self):
        self.groups_worker = None
        self.groups_thread = None
        
    def filter_stories(
    self,
    text: str
):
        query = text.strip().casefold()

        for category_index in range(
            self.stories_tree.topLevelItemCount()
        ):

            category_item = (
                self.stories_tree.topLevelItem(
                    category_index
                )
            )

            category_matches = (
                query
                and query
                in category_item.text(0).casefold()
            )

            visible_children = 0

            for child_index in range(
                category_item.childCount()
            ):

                child = category_item.child(
                    child_index
                )

                group_id = child.data(
                    0,
                    Qt.ItemDataRole.UserRole
                )

                title = child.text(
                    0
                ).casefold()

                group_id_text = str(
                    group_id
                ).casefold()

                matches = (
                    not query
                    or category_matches
                    or query in title
                    or query in group_id_text
                )

                child.setHidden(
                    not matches
                )

                if matches:
                    visible_children += 1

            category_item.setHidden(
                visible_children == 0
            )

            if query and visible_children:
                category_item.setExpanded(
                    True
                )
                
    def toggle_all_stories(self):

        story_items = []

        for category_index in range(
            self.stories_tree.topLevelItemCount()
        ):
            category_item = (
                self.stories_tree.topLevelItem(
                    category_index
                )
            )

            for child_index in range(
                category_item.childCount()
            ):
                story_items.append(
                    category_item.child(
                        child_index
                    )
                )

        if not story_items:
            return

        all_selected = all(
            item.checkState(0)
            == Qt.CheckState.Checked
            for item in story_items
        )

        new_state = (
            Qt.CheckState.Unchecked
            if all_selected
            else Qt.CheckState.Checked
        )

        for item in story_items:
            item.setCheckState(
                0,
                new_state
            )