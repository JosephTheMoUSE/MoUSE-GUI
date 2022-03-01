import configparser
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional

from mouseapp.controller.utils import warn_user
from mouseapp.model.main_models import ApplicationModel, MainModel, \
    ProjectModel, SpectrogramModel
from mouseapp.model.settings.settings_model import SettingsModel
from mouseapp.model.utils import MouseProject

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)
import deepdish as dd  # noqa

warnings.resetwarnings()


def _add_project_data_filename(project_path: Path):
    """Add a filename under which general model data is stored."""
    return project_path.joinpath("project_data.h5")


def _add_mouse_identifier_filename(project_path: Path):
    """Add a unique filename that can identify mouse projects."""
    return project_path.joinpath(".mouse_project.txt")


def _is_mouse_project(project_path: Path):
    """Check for existence of a special mouse project file."""
    mouse_unique_file = _add_mouse_identifier_filename(project_path)
    return mouse_unique_file.exists()


def save_project(model: MainModel):
    """Save `model` to a file.

    As a part of saving the model, the project is set as a most recent project
    in `ApplicationModel`.
    App configuration is also saved.
    """
    project_path = model.project_model.project_path
    if project_path.exists() and not _is_mouse_project(project_path):
        warn_user(model,
                  "Application can't be saved under"
                  "already existing folder!")
        return ""

    project_save_path = _add_project_data_filename(project_path)

    if not project_path.exists():
        # initialize project folder
        project_path.mkdir(parents=True)
        _add_mouse_identifier_filename(project_path).touch()

    # save project's data
    model_dict = model.to_dict()
    dd.io.save(project_save_path, model_dict)

    # Update recent project if needed
    if model.application_model.recent_project is None or \
            model.application_model.recent_project.path != project_path:
        model.application_model.recent_project = MouseProject(
            name=model.project_model.project_name, path=project_path)
        save_config(model.application_model)

    current_time = datetime.now().strftime("%H:%M")
    return f"Project saved - {current_time}"


def load_project(app_model: ApplicationModel, project_path: Path) \
        -> Optional[MainModel]:
    """Load `model` from a file in directory `project_path` if possible."""
    model = MainModel(application_model=app_model,
                      spectrogram_model=SpectrogramModel(),
                      project_model=ProjectModel(),
                      settings_model=SettingsModel())

    project_save_path = _add_project_data_filename(project_path)
    try:
        model_dict = dd.io.load(project_save_path)
        model.from_dict(model_dict)
        return model
    except Exception as e:
        logging.warning(f"Project couldn't be loaded from {project_save_path}"
                        f"Exception raised: {e}")
        return None


def save_config(app_model: ApplicationModel):
    """Save app configuration into a file."""
    app_config_path = app_model.app_config_file
    if not app_config_path.parent.exists():
        # todo (#45): manage situations when the path already exists, but is not
        #           correct (e.g. folder instead of file)
        app_config_path.parent.mkdir(parents=True)

    config = configparser.ConfigParser()
    config['CONFIGURATION'] = {
        'user_projects':
            str({str(project) for project in app_model.user_projects}),
        'last_project':
            str(app_model.recent_project)
    }
    with app_config_path.open('w') as fp:
        config.write(fp)


def change_model_path(model, new_path):
    # todo (#56): change the model path to new_path
    raise NotImplementedError


def save_project_as(folder: Path, model: MainModel):
    project_path = folder.joinpath(model.project_model.project_name)
    change_model_path(model=model, new_path=project_path)


def _get_project_name(app_model: ApplicationModel, project_path: Path) \
        -> Optional[str]:
    if not _is_mouse_project(project_path):
        raise ValueError("Can't get name of a not-MoUSE project!")
    model = load_project(app_model, project_path)
    if isinstance(model, MainModel):
        return model.project_model.project_name
    return None


def update_projects(model: MainModel, folder: str):
    """Load mouse project from disk."""
    project_path = Path(folder)
    if not _is_mouse_project(project_path):
        warn_user(model, "Select MoUSE project!")
        return False

    project_name = _get_project_name(app_model=model.application_model,
                                     project_path=project_path)
    if project_name is None:
        warn_user(
            model,
            "This project is damaged or incompatible with "
            "current version of MoUSE!")
        return False
    model.application_model.user_projects.add(
        MouseProject(name=project_name, path=project_path))
    save_config(model.application_model)
    return True
