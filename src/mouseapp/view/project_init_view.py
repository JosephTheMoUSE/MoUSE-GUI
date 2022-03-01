import logging
from functools import partial
from pathlib import Path
from typing import Optional

import mouseapp.controller.utils
from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6.QtWidgets import QListWidgetItem, QStackedLayout
from mouseapp import context_manager
from mouseapp.controller import main_controller
from mouseapp.controller import persistency_controller
from mouseapp.controller.utils import warn_user
from mouseapp.model.main_models import MainModel
from mouseapp.view.generated.init_project.ui_basic_metadata_widget import \
    Ui_BasicMetadataWidget
from mouseapp.view.generated.init_project.ui_load_audio_widget import \
    Ui_LoadAudioWidget
from mouseapp.view.generated.init_project.ui_main_window \
    import Ui_CreateProjectWindow
from mouseapp.view.generated.init_project.ui_select_project \
    import Ui_SelectProject
from mouseapp.view.widgets import ProjectEntry


class SelectProject(QtWidgets.QWidget, Ui_SelectProject):
    """Select Project widget class.

    This class represents a window which contains:
    - a list of projects
    - a button which allows to load a project from the list
    - a button which allows to add from disk a project to the list of projects
    """

    def __init__(self,
                 next_model: MainModel,
                 old_model: MainModel,
                 old_widget: QtWidgets.QWidget):
        super(SelectProject, self).__init__()
        self.setupUi(self)

        self.next_model = next_model
        self.old_model = old_model
        self._selected_project_path: Optional[Path] = None

        # Setup the list of existing projects
        self._setup_project_list()

        # Connect buttons
        self.projectsList.itemClicked.connect(self._on_project_item_clicked)
        self.loadProjectButton.clicked.connect(
            partial(self._on_load_project,
                    old_model=old_model,
                    old_widget=old_widget))
        self.selectFromDiskButton.clicked.connect(self._on_select_from_disk)

    def _on_project_item_clicked(self, widget: QListWidgetItem):
        """Enable `loadProjectButton` and set selected project."""
        self.loadProjectButton.setEnabled(True)
        project_entry = widget.data(0)
        logging.debug(f"[Project manager] Project pre-selected for loading: "
                      f"{project_entry}")

        if isinstance(project_entry, ProjectEntry):
            logging.debug("[Project manager] Project selection was accepted."
                          f"Selected project info: "
                          f"{project_entry.mouse_project}")
            self._selected_project_path = project_entry.mouse_project.path
        else:
            mouseapp.controller.utils.warn_user(self.model,
                                                "Project can't be loaded!")
            self.loadProjectButton.setEnabled(False)

    def _on_load_project(self, old_model, old_widget):
        """Load next model and close creation window."""
        assert self._selected_project_path is not None
        next_model = persistency_controller.load_project(
            app_model=old_model.application_model,
            project_path=self._selected_project_path)
        if next_model is None:
            warn_user(old_model, "Project failed to load!")
            return
        context_manager.switch_projects(next_model=next_model,
                                        old_model=old_model,
                                        old_widget=old_widget)
        self.close()

    def _on_select_from_disk(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Select MoUSE project',
            self.next_model.application_model.app_data_dir.__str__(),
            QtWidgets.QFileDialog.ShowDirsOnly |
            QtWidgets.QFileDialog.DontResolveSymlinks)
        persistency_controller.update_projects(self.next_model, folder)
        self._selected_project_path: Optional[Path] = None
        self.projectsList.clear()
        self._setup_project_list()

    def _setup_project_list(self):
        self.loadProjectButton.setEnabled(False)

        for mouse_project in self.next_model.application_model.user_projects:
            if (self.old_model.project_model is None or mouse_project.path
                    == self.old_model.project_model.project_path):
                continue
            project_entry = ProjectEntry(mouse_project=mouse_project)

            project_list_item = QListWidgetItem(self.projectsList)
            project_list_item.setData(0, project_entry)
            project_list_item.setSizeHint(project_entry.sizeHint())
            self.projectsList.addItem(project_list_item)
            self.projectsList.setItemWidget(project_list_item, project_entry)

    def closeEvent(self, event):
        self.parent().close()


class BasicMetadata(QtWidgets.QWidget, Ui_BasicMetadataWidget):
    """Basic Metadata widget class."""

    def __init__(self, model):
        super(BasicMetadata, self).__init__()
        self.setupUi(self)

        # Connect buttons
        self.projectNameEdit.textChanged.connect(
            lambda: main_controller.set_project_name(
                model=model, name=self.projectNameEdit.text()))
        self.dateEdit.dateChanged.connect(
            lambda: main_controller.set_experiment_date(
                model=model, date=self.dateEdit.date()))
        self.noteEdit.textChanged.connect(
            lambda: main_controller.set_project_note(
                model=model, note=self.noteEdit.toPlainText()))


class LoadAudio(QtWidgets.QWidget, Ui_LoadAudioWidget):
    """Load audio widget class."""

    def __init__(self, model):
        super(LoadAudio, self).__init__()
        self.setupUi(self)
        self.model = model

        # Connect buttons
        self.loadFilesButton.clicked.connect(self._on_load_audio_files)
        self.loadFolderButton.clicked.connect(
            lambda: self._on_load_audio_files(folder=True))

        # Connect signals
        self.model.project_model.audio_files_changed.connect(
            self._on_audio_files_changed)

    def _on_load_audio_files(self, folder=False):
        # todo (#39): show only folders in File Dialog
        if folder:
            files = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                'Select audio files',
                Path('').__str__(),
                QtWidgets.QFileDialog.ShowDirsOnly |
                QtWidgets.QFileDialog.DontResolveSymlinks)
            main_controller.load_audio_files(model=self.model,
                                             files=files,
                                             folder=True)
        else:
            files = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                'Select audio files',
                Path('').__str__(),
                'Audio files (*.wav *.mp3)')[0]
            main_controller.load_audio_files(model=self.model, files=files)

    def _on_audio_files_changed(self, value):
        self.fileLoadingStatusInfo.setText(f'Loaded {value} audio files.')


class InitializeProjectWindow(QtWidgets.QWidget, Ui_CreateProjectWindow):
    """Create Initialize Project Window class."""

    def __init__(self,
                 next_model: MainModel,
                 old_model: MainModel,
                 old_widget,
                 start_from_creation: bool = False):
        super(InitializeProjectWindow, self).__init__()
        self.setupUi(self)

        # Makes the new window stay on top of the application
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.next_model = next_model
        self.next_model.application_model.active_windows.add(self)
        self.project_finished = False

        # Initialize widgets
        self.select_project_widget = SelectProject(next_model=next_model,
                                                   old_model=old_model,
                                                   old_widget=old_widget)
        self.select_project_widget.setParent(self)
        self.basic_metadata_widget = BasicMetadata(model=next_model)
        self.load_audio_widget = LoadAudio(model=next_model)

        # Setup layout
        self.initialization_layout = QStackedLayout()
        for widget in [
                self.select_project_widget,
                self.basic_metadata_widget,
                self.load_audio_widget
        ]:
            self.initialization_layout.addWidget(widget)
        self.setLayout(self.initialization_layout)

        if start_from_creation:
            self.initialization_layout.setCurrentWidget(
                self.basic_metadata_widget)
        else:
            self.initialization_layout.setCurrentWidget(
                self.select_project_widget)

        # Connect next/previous buttons
        self.select_project_widget.newProjectButton.clicked.connect(
            partial(self.initialization_layout.setCurrentWidget,
                    self.basic_metadata_widget))
        self.basic_metadata_widget.buttonNext.clicked.connect(
            self._on_basic_metadata_button_next)
        self.load_audio_widget.buttonPrevious.clicked.connect(
            partial(self.initialization_layout.setCurrentWidget,
                    self.basic_metadata_widget))
        self.load_audio_widget.buttonFinish.clicked.connect(
            partial(self._button_finish_clicked,
                    next_model=next_model,
                    old_model=old_model,
                    old_widget=old_widget))

    def _button_finish_clicked(self, next_model, old_model, old_widget):
        """Finalize creation of a new model and close creation window."""
        context_manager.finalize_project_creation(next_model=next_model,
                                                  old_model=old_model,
                                                  old_widget=old_widget)
        self.close()

    def closeEvent(self, event):
        if self in self.next_model.application_model.active_windows:
            self.next_model.application_model.active_windows.remove(self)
        if self.project_finished:
            persistency_controller.save_project(self.next_model)
        event.accept()

    def _on_basic_metadata_button_next(self):
        if self.next_model.project_model.project_name == "":
            mouseapp.controller.utils.warn_user(self.next_model,
                                                "Project name can't be empty!")
        else:
            self.initialization_layout.setCurrentWidget(self.load_audio_widget)
