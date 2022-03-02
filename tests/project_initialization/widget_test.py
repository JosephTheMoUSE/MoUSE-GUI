from copy import copy

from mouseapp.view.main_view import MainWindow
from mouseapp.view.project_init_view import BasicMetadata, InitializeProjectWindow
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


def test_basic_metadata_widget(qtbot, tmpdir, clean_main_model):
    metadata_widget = BasicMetadata(model=clean_main_model)

    qtbot.addWidget(metadata_widget)

    qtbot.keyClicks(metadata_widget.projectNameEdit, "test-project-name")
    long_note = " This is a veeeeeeeeery long note!" * 100
    qtbot.keyClicks(metadata_widget.noteEdit, long_note)

    assert clean_main_model.project_model.project_name == "test-project-name"
    assert clean_main_model.project_model.experiment_note == long_note
