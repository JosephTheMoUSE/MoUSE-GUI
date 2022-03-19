from pathlib import Path
from unittest import mock

from mouseapp.model.utils import MouseProject
from mouseapp.controller import persistency_controller
from mouseapp.model.main_models import ApplicationModel
from mouseapp.view.main_view import MainWindow
from tests.model_fixtures import *  # noqa


def test_load_config(app_model, tmpdir):
    """Tests whether the config is saved and loaded correctly."""
    base_dir = Path(tmpdir)
    app_model.recent_project = MouseProject(name="project_recent",
                                            path=base_dir.joinpath("project_recent"))
    app_model.user_projects = {
        app_model.recent_project,
        MouseProject(name="project_other", path=base_dir.joinpath("project_other")),
    }
    persistency_controller.save_config(app_model)

    # here application is closed and opened again...

    with mock.patch(
            "mouseapp.model.main_models.appdirs.user_config_dir",
            mock.MagicMock(return_value=str(tmpdir)),
    ):
        with mock.patch(
                "mouseapp.model.main_models.appdirs.user_config_dir",
                mock.MagicMock(return_value=str(tmpdir)),
        ):
            reopened_app_model = ApplicationModel()

    assert reopened_app_model.recent_project == app_model.recent_project
    assert reopened_app_model.user_projects == app_model.user_projects


def test_load_model(main_model):
    """Tests whether the project is saved and loaded correctly."""
    main_model.application_model.recent_project = None
    persistency_controller.save_project(main_model)
    assert main_model.application_model.recent_project is not None
    assert (main_model.application_model.recent_project.path ==
            main_model.project_model.project_path)

    # here application is closed and opened again...

    app_model = main_model.application_model
    loaded_model = persistency_controller.load_project(
        app_model=app_model, project_path=app_model.recent_project.path)

    assert loaded_model.to_dict() == main_model.to_dict()


def test_action_save(qtbot, main_model):
    """Tests saving triggered by `actionSave` from menubar."""
    widget = MainWindow(main_model)
    qtbot.addWidget(widget)

    widget.actionSave.trigger()

    app_model = main_model.application_model
    loaded_model = persistency_controller.load_project(
        app_model=app_model, project_path=app_model.recent_project.path)

    assert main_model.to_dict() == loaded_model.to_dict()


def test_project_saves_on_close_event(main_model, qtbot):
    """Tests whether the project is saved when the app is closed."""
    assert not main_model.project_model.project_path.exists()
    widget = MainWindow(main_model)
    qtbot.addWidget(widget)

    widget.close()

    app_model = main_model.application_model
    loaded_model = persistency_controller.load_project(app_model,
                                                       app_model.recent_project.path)

    assert main_model.to_dict() == loaded_model.to_dict()
