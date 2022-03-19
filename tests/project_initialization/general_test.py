from copy import copy
from pathlib import Path

from pytestqt.qt_compat import qt_api

from mouseapp.controller import persistency_controller
from mouseapp.model.main_models import MainModel
from mouseapp.model.settings.settings_model import SettingsModel
from mouseapp.view.main_view import MainWindow
from mouseapp.view.project_init_view import InitializeProjectWindow
from tests.model_fixtures import *  # noqa F401 F403


def trigger_action_get_window(action, main_model):
    active_before = copy(main_model.application_model.active_windows)
    action.trigger()
    new_active = main_model.application_model.active_windows - active_before
    assert len(new_active) == 1
    return new_active.pop()


def test_new_project_action(qtbot, main_model):
    main_window = MainWindow(main_model)
    qtbot.addWidget(main_window)

    new_widget = trigger_action_get_window(action=main_window.actionNewProject,
                                           main_model=main_model)

    assert isinstance(new_widget, InitializeProjectWindow)
    assert new_widget.isVisible()
    assert not new_widget.select_project_widget.isVisible()
    assert new_widget.basic_metadata_widget.isVisible()


def test_load_project_action(qtbot, main_model):
    main_window = MainWindow(main_model)
    qtbot.addWidget(main_window)

    new_widget = trigger_action_get_window(action=main_window.actionLoadProject,
                                           main_model=main_model)
    assert isinstance(new_widget, InitializeProjectWindow)
    assert new_widget.isVisible()
    assert new_widget.select_project_widget.isVisible()
    assert not new_widget.select_project_widget.newProjectButton.isVisible()


def test_new_project(qtbot, tmpdir, main_model, clean_project_model, clean_spec_model):
    old_widget = MainWindow(model=main_model)
    next_model = MainModel(
        application_model=generate_app_model(Path(tmpdir)),  # noqa F405
        project_model=clean_project_model,
        spectrogram_model=clean_spec_model,
        settings_model=SettingsModel(),
    )
    initialization_window = InitializeProjectWindow(next_model=next_model,
                                                    old_model=main_model,
                                                    old_widget=old_widget)
    qtbot.addWidget(old_widget)
    qtbot.addWidget(initialization_window)

    qtbot.keyClicks(initialization_window.basic_metadata_widget.projectNameEdit,
                    "test-project-name")
    qtbot.mouseClick(
        initialization_window.basic_metadata_widget.buttonNext,
        qt_api.QtCore.Qt.MouseButton.LeftButton,
    )

    assert not main_model.project_model.project_path.exists()
    qtbot.mouseClick(
        initialization_window.load_audio_widget.buttonFinish,
        qt_api.QtCore.Qt.MouseButton.LeftButton,
    )
    assert (persistency_controller.load_project(
        project_path=main_model.project_model.project_path,
        app_model=main_model.application_model,
    ).to_dict() == main_model.to_dict())
    assert not old_widget.isVisible()
    assert next_model.project_model.project_name == "test-project-name"
    assert (next_model.application_model.recent_project.path ==
            next_model.project_model.project_path)
