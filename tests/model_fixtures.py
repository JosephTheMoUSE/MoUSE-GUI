"""Fixtures of `model`s and paths needed for their configuration."""

from pathlib import Path
from unittest import mock

import pytest
from PySide6 import QtCore

from mouseapp.model.main_models import ApplicationModel, MainModel, \
    ProjectModel, SpectrogramModel
from mouseapp.model.settings.settings_model import SettingsModel

# regex for generating `__all__` list:
#   '@pytest.fixture\ndef (\w+)[(){}\[\]\-.,\w\t\s:'"=#]*'
__all__ = [
    'generate_app_model',
    'path_tmpdir',
    'app_model',
    'project_model',
    'spec_model',
    'main_model',
    'clean_app_model',
    'clean_project_model',
    'clean_spec_model',
    'clean_main_model',
    'empty_main_model',
]


def generate_app_model(temporary_path: Path):

    with mock.patch('mouseapp.model.main_models.appdirs.user_config_dir',
                    mock.MagicMock(return_value=str(temporary_path))):
        with mock.patch('mouseapp.model.main_models.appdirs.user_data_dir',
                        mock.MagicMock(return_value=str(temporary_path))):
            application_model = ApplicationModel()
    return application_model


@pytest.fixture
def path_tmpdir(tmpdir):
    return Path(tmpdir)


@pytest.fixture
def app_model(tmpdir):
    return generate_app_model(temporary_path=Path(tmpdir))


@pytest.fixture
def project_model(path_tmpdir):
    project_model = ProjectModel()
    project_model._project_name = 'project_name'
    project_model._project_path = path_tmpdir.joinpath(
        project_model.project_name)
    project_model._experiment_note = '42'
    project_model._experiment_date = QtCore.QDate(2136, 6, 17)
    project_model._audio_files = [
        path_tmpdir.joinpath('audio_23.wav'),
        path_tmpdir.joinpath('audio_17.wav')
    ]
    project_model._project_metadata = {
        'key-1': ('value', 'Text'),
        'key-2': (4.2, 'Real'),
        'key3': (1, 'Integer'),
        '4key': (1, 'Integer')
    }
    return project_model


@pytest.fixture
def spec_model(tmpdir):
    project_model = SpectrogramModel()
    # todo: when spectrogram model gets attributes they should be set here
    return project_model


@pytest.fixture
def main_model(app_model, spec_model, project_model):
    return MainModel(application_model=app_model,
                     spectrogram_model=spec_model,
                     project_model=project_model,
                     settings_model=SettingsModel())


@pytest.fixture
def clean_app_model(tmpdir):
    temporary_path = Path(tmpdir).joinpath('dont_save_here')
    assert not temporary_path.joinpath('config.ini').exists()
    return generate_app_model(temporary_path=temporary_path)


@pytest.fixture
def clean_project_model():
    return ProjectModel()


@pytest.fixture
def clean_spec_model():
    return SpectrogramModel()


@pytest.fixture
def clean_main_model(clean_app_model, clean_project_model, clean_spec_model):
    return MainModel(application_model=clean_app_model,
                     project_model=clean_project_model,
                     spectrogram_model=clean_spec_model,
                     settings_model=SettingsModel())


@pytest.fixture
def empty_main_model(clean_app_model):
    return MainModel(application_model=clean_app_model,
                     project_model=None,
                     spectrogram_model=None,
                     settings_model=None)
