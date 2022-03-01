from mouseapp.model.main_models import MainModel, ProjectModel, \
    SpectrogramModel
from mouseapp.model.utils import SerializableModel
from mouseapp.model.settings.settings_model import SettingsModel
from tests.model_fixtures import *  # noqa F401 F403


def test_project_model(project_model):
    """Tests whether project model is serialized and deserialized correctly."""
    assert isinstance(project_model, SerializableModel)

    serialized = project_model.to_dict()
    new_model = ProjectModel()
    new_model.from_dict(serialized)

    assert project_model._project_name == new_model._project_name
    assert project_model._project_path == new_model._project_path
    assert project_model._project_metadata == new_model._project_metadata
    assert project_model._audio_files == new_model._audio_files
    assert project_model._experiment_note == new_model._experiment_note
    assert project_model._experiment_date == new_model._experiment_date


def test_main_model(main_model, app_model):
    """Tests whether main model is serialized and deserialized correctly.

    This test includes testing all `SerializableModel`s from the main model.
    """
    serialized = main_model.to_dict()

    new_main_model = MainModel(application_model=app_model,
                               project_model=ProjectModel(),
                               spectrogram_model=SpectrogramModel(),
                               settings_model=SettingsModel())
    new_main_model.from_dict(serialized)

    def assert_equal_models(model: SerializableModel,
                            new_model: SerializableModel):
        for attr_name in dir(model):
            assert set(dir(model)) == set(dir(new_model))
            if not model._is_settable_attribute(attr_name):
                continue
            assert getattr(model, attr_name) == getattr(new_model, attr_name)

    assert isinstance(main_model.project_model, SerializableModel)
    assert isinstance(new_main_model.project_model, SerializableModel)
    assert_equal_models(main_model.project_model, new_main_model.project_model)

    assert isinstance(main_model.spectrogram_model, SerializableModel)
    assert isinstance(new_main_model.spectrogram_model, SerializableModel)
    assert_equal_models(main_model.spectrogram_model,
                        new_main_model.spectrogram_model)
