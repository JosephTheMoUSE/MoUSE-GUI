"""This module is intended for logic closely related with window initialization."""  # noqa
import sys
from typing import Optional

from PySide6 import QtWidgets
from PySide6.QtWidgets import QMainWindow
from mouseapp.controller import persistency_controller
from mouseapp.model.main_models import ApplicationModel, MainModel
from mouseapp.model.main_models import ProjectModel, SpectrogramModel
from mouseapp.model.settings.settings_model import SettingsModel
from mouseapp.model.utils import MouseProject
from mouseapp.view.utils import initialize_widget


def initialize_application():
    """Start the application.

    First opened window depends on the existence of 'recent project path' in the
    MoUSE config file. If the path exists `MainWindow` is opened, otherwise
    project initialization window is opened.
    """
    application = QtWidgets.QApplication.instance()
    if not application:
        application = QtWidgets.QApplication(sys.argv)

    if not initialize_from_existing():
        initialize_new()

    sys.exit(application.exec()) #_exec()
    #above, we used the newest version of running the main window of the app (using PySide6)


def initialize_from_existing() -> bool:
    from mouseapp.view.main_view import MainWindow

    app_model = ApplicationModel()

    if app_model.recent_project is not None:
        model = persistency_controller.load_project(
            app_model=app_model, project_path=app_model.recent_project.path)
        if model is not None:
            initialize_widget(MainWindow(model=model))
            model.project_model.emit_all_setting_signals()

            return True
    return False


def initialize_new():
    old_model = MainModel(
        application_model=ApplicationModel(),
        spectrogram_model=None,
        project_model=None,
        settings_model=None,
    )

    next_model = MainModel(
        application_model=old_model.application_model,
        spectrogram_model=SpectrogramModel(),
        project_model=ProjectModel(),
        settings_model=SettingsModel(),
    )

    from mouseapp.view.project_init_view import InitializeProjectWindow

    initialize_widget(
        InitializeProjectWindow(next_model=next_model,
                                old_model=old_model,
                                old_widget=None))


def instantiate_project_creation_window(old_model, old_widget):
    """Instantiate project creation window.

    The window instantiated is `InitializeProjectWindow` with first project
    creation widget selected.
    """
    from mouseapp.view.project_init_view import InitializeProjectWindow

    next_model = MainModel(
        application_model=old_model.application_model,
        project_model=ProjectModel(),
        spectrogram_model=SpectrogramModel(),
        settings_model=SettingsModel(),
    )

    initialize_project = initialize_widget(
        InitializeProjectWindow(
            next_model=next_model,
            old_model=old_model,
            old_widget=old_widget,
            start_from_creation=True,
        ))
    return initialize_project


def instantiate_project_load_window(old_model, old_widget):
    """Instantiate window with a list of existing projects.

    The window instantiated is `InitializeProjectWindow` with disabled
    `newProjectButton`.
    """
    from mouseapp.view.project_init_view import InitializeProjectWindow

    next_model = MainModel(
        application_model=old_model.application_model,
        spectrogram_model=SpectrogramModel(),
        project_model=ProjectModel(),
        settings_model=SettingsModel(),
    )

    initialize_project = initialize_widget(
        InitializeProjectWindow(next_model=next_model,
                                old_model=old_model,
                                old_widget=old_widget))
    initialize_project.select_project_widget.newProjectButton.hide()
    return initialize_project


def switch_projects(
    next_model: MainModel,
    old_model: MainModel,
    old_widget: Optional[QMainWindow] = None,
):
    """Close old model & main window, open new model & main window.

    Responsibilities of this function:
     - save old model (unless only `ApplicationModel` is instantiated)
     - close previous instance of `MainWindow` (if any)
     - set recent project
     - assert that project related to `next_model` is in `user_projects` list
     - create new instance of `MainWindow` and add a reference to it to
     `ApplicationModel`
    """
    if old_model.spectrogram_model is not None or old_model.project_model is not None:
        assert old_widget is not None
        if old_model is None:
            raise TypeError("When `old_model` is set `old_widget` can't be None")

        old_widget.close()

    from mouseapp.view.main_view import MainWindow

    mouse_project = MouseProject(
        name=next_model.project_model.project_name,
        path=next_model.project_model.project_path,
    )
    next_model.application_model.user_projects.add(mouse_project)
    next_model.application_model.recent_project = mouse_project
    persistency_controller.save_config(app_model=next_model.application_model)
    initialize_widget(MainWindow(model=next_model))
    next_model.project_model.emit_all_setting_signals()


def finalize_project_creation(
    next_model: MainModel,
    old_model: MainModel,
    old_widget: Optional[QtWidgets.QMainWindow] = None,
):
    """Set project path in project model and switch projects."""
    next_model.project_model.project_path = (
        next_model.application_model.app_data_dir.joinpath(
            next_model.project_model.project_name))
    switch_projects(next_model=next_model, old_model=old_model, old_widget=old_widget)
