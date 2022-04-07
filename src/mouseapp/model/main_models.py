from __future__ import annotations

import configparser
import datetime
import logging
from pathlib import Path
from torchaudio.transforms import Spectrogram
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple

import appdirs
from PySide6.QtCore import QDate, QObject, Signal, QMutex, QModelIndex
from mouse.utils.sound_util import SpectrogramData
from mouseapp.model import constants
from mouseapp.model.settings.settings_model import SettingsModel
from mouseapp.model.utils import BackgroundTask, Annotation, SerializableModel
from mouseapp.model.utils import MouseProject
from mouseapp.model.annotation_table_model import AnnotationTableModel


class ProjectModel(SerializableModel):
    """Project Model class.

    Used for project creation.
    """

    # signals
    audio_files_changed = Signal(int)
    project_metadata_added = Signal(tuple)
    project_metadata_removed = Signal(dict)
    project_metadata_updated = Signal(tuple)

    audio_files_signal = Signal(list)
    project_name_signal = Signal(str)
    experiment_date_signal = Signal(QDate)
    experiment_note_signal = Signal(str)
    project_metadata_signal = Signal(dict)

    def __init__(self, audio_files: Optional[List[Path]] = None):
        super().__init__()

        if audio_files is None:
            audio_files = list()
        self._audio_files: List[Path] = audio_files
        self._audio_files_attr_name = "audio_files"
        self._project_name = ""
        self._experiment_date: Optional[QDate] = None
        self._experiment_date_attr_name = "experiment_date"
        self._experiment_note = ""
        self._project_metadata: Dict[str, Tuple[Any, str]] = dict()
        self._project_path: Optional[Path] = None
        self._project_path_attr_name = "project_path"

    @property
    def audio_files(self):
        return self._audio_files

    @audio_files.setter
    def audio_files(self, list_of_files):
        self._audio_files = list_of_files
        self.audio_files_changed.emit(len(self.audio_files))

    @property
    def project_name(self):
        return self._project_name

    @project_name.setter
    def project_name(self, project_name):
        self._project_name = project_name

    @property
    def experiment_date(self):
        return self._experiment_date

    @experiment_date.setter
    def experiment_date(self, experiment_date):
        self._experiment_date = experiment_date

    @property
    def experiment_note(self):
        return self._experiment_note

    @experiment_note.setter
    def experiment_note(self, experiment_note):
        self._experiment_note = experiment_note

    @property
    def project_path(self):
        return self._project_path

    @project_path.setter
    def project_path(self, value):
        self._project_path = value

    @property
    def project_metadata(self):
        return self._project_metadata

    @project_metadata.setter
    def project_metadata(self, project_metadata):
        self._project_metadata = project_metadata

    def add_project_metadata(self, key_value_type):
        self.project_metadata[key_value_type[0]] = (
            key_value_type[1],
            key_value_type[2],
        )
        self.project_metadata_added.emit(key_value_type)

    def update_project_metadata(self, key_value_type):
        self.project_metadata[key_value_type[0]] = (
            key_value_type[1],
            key_value_type[2],
        )
        self.project_metadata_updated.emit(key_value_type)

    def remove_project_metadata(self, key):
        self.project_metadata.pop(key)
        self.project_metadata_removed.emit(self.project_metadata)

    def emit_all_setting_signals(self):
        self.project_name_signal.emit(self.project_name)
        self.audio_files_signal.emit(self.audio_files)
        self.experiment_note_signal.emit(self.experiment_note)
        if self.experiment_date is not None:
            self.experiment_date_signal.emit(self.experiment_date)
        if len(self.project_metadata) > 0:
            self.project_metadata_signal.emit(self.project_metadata)

    def remove_audio_file(self, file_name):
        for full_file_name in self.audio_files:
            if str(full_file_name).endswith(file_name):
                self.audio_files.remove(full_file_name)
                break
        self.audio_files_signal.emit(self.audio_files)

    def _value_to_dict(self, name, value):
        if name == self._audio_files_attr_name:
            return [str(path) for path in value]
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, QDate):
            return value.toString("yyyy.MM.dd")
        return value

    def _value_from_dict(self, name, value):
        if name == self._audio_files_attr_name:
            return [Path(path) for path in value]
        if name == self._project_path_attr_name:
            return Path(value)
        if name == self._experiment_date_attr_name and isinstance(value, str):
            return QDate.fromString(value, "yyyy.MM.dd")
        return value


class SpectrogramModel(SerializableModel):
    """Spectrogram Model class."""

    spectrogram_display_size_changed = Signal(int)
    slider_step_size_changed = Signal(int)
    spectrogram_data_changed = Signal(tuple)
    spectrogram_chunk_data_changed = Signal(SpectrogramData)
    visible_annotations_changed = Signal(tuple)
    # annotations_info_signal = Signal(tuple) # todo(werkaaa): remove
    # annotation_field_changed = Signal(tuple) # todo(werkaaa): remove

    progressbar_changed = Signal(tuple)
    detection_info_changed = Signal(tuple)
    detection_allowed_changed = Signal(bool)
    select_annotations = Signal(list)

    def __init__(self):
        super().__init__()
        # Spectrogram generation parameters
        self.n_fft = 512
        self.win_length = 512
        self.hop_length = 256
        self.center = True
        self.pad_mode = "reflect"
        self.power = 1
        self.sample_rate = None
        self.spectrogram_calculator: Optional[Spectrogram] = None
        self._spectrogram_data: Optional[SpectrogramData] = None

        # Annotations
        # This model is later overwritten in view
        self._annotation_table_model = AnnotationTableModel(self)

        # Visualization parameters
        self._spectrogram_display_size = 1000  # time in milliseconds
        self._slider_step_size = self._spectrogram_display_size / 20
        self._annotation_margin = self._spectrogram_display_size / 20
        self._current_spectrogram_chunk_data: Optional[SpectrogramData] = None
        self._visible_annotations: List[Annotation] = []
        self.time_mask = None

        # Parameters related to long spectrogram operations
        self.detection_mutex = QMutex()
        self.background_task: Optional[BackgroundTask] = None
        self._progressbar_exists: bool = False
        self._progressbar_primary_text: Optional[str] = None
        self._progressbar_secondary_text: Optional[str] = None
        self._progressbar_count: Optional[int] = None
        self._progressbar_progress: Optional[int] = None
        self._detection_allowed: bool = True

        # SerializableModel setup
        self._dict_denylist.update([
            "spectrogram_data",
            "spectrogram_calculator",
            "time_mask",
            "current_spectrogram_chunk_data",
            "visible_annotations",
            "current_spectrogram_chunk_data",
            "spectrogram_data",
            "visible_annotations",
            "detection_mutex",
            "progressbar_primary_text",
            "progressbar_secondary_text",
            "progressbar_count",
            "progressbar_progress",
            "progressbar_exists",
        ])

    @property
    def annotation_margin(self):
        return self._annotation_margin

    @annotation_margin.setter
    def annotation_margin(self, value):
        self._annotation_margin = value

    @property
    def detection_allowed(self) -> bool:
        return self._detection_allowed

    @detection_allowed.setter
    def detection_allowed(self, value: bool):
        self._detection_allowed = value
        self.detection_allowed_changed.emit(value)

    @property
    def progressbar_progress(self) -> Optional[int]:
        return self._progressbar_progress

    @progressbar_progress.setter
    def progressbar_progress(self, value: Optional[int]):
        self._progressbar_progress = value
        self.detection_info_changed.emit((
            self._progressbar_primary_text,
            self._progressbar_progress,
            self._progressbar_secondary_text,
        ))

    @property
    def progressbar_exists(self):
        return self._progressbar_exists

    @progressbar_exists.setter
    def progressbar_exists(self, value):
        self._progressbar_exists = value
        self.progressbar_changed.emit(value)

    @property
    def progressbar_primary_text(self):
        return self._progressbar_primary_text

    @progressbar_primary_text.setter
    def progressbar_primary_text(self, value):
        self._progressbar_primary_text = value
        self.detection_info_changed.emit((
            self._progressbar_primary_text,
            self._progressbar_progress,
            self._progressbar_secondary_text,
        ))

    @property
    def progressbar_secondary_text(self):
        return self._progressbar_secondary_text

    @progressbar_secondary_text.setter
    def progressbar_secondary_text(self, value):
        self._progressbar_secondary_text = value
        self.detection_info_changed.emit((
            self._progressbar_primary_text,
            self._progressbar_progress,
            self._progressbar_secondary_text,
        ))

    @property
    def progressbar_count(self):
        return self._progressbar_count

    @progressbar_count.setter
    def progressbar_count(self, value):
        self._progressbar_count = value

    @property
    def current_spectrogram_chunk_data(self):
        return self._current_spectrogram_chunk_data

    @current_spectrogram_chunk_data.setter
    def current_spectrogram_chunk_data(self, spectrogram_chunk):
        self._current_spectrogram_chunk_data = spectrogram_chunk
        self.spectrogram_chunk_data_changed.emit(spectrogram_chunk)

    @property
    def spectrogram_data(self) -> Optional[SpectrogramData]:
        return self._spectrogram_data

    @spectrogram_data.setter
    def spectrogram_data(self, spectrogram_data):
        self._spectrogram_data = spectrogram_data
        self.time_mask = None  # invalidate time mask
        self.spectrogram_data_changed.emit(
            (self._spectrogram_data, self._spectrogram_display_size))

    @property
    def spectrogram_display_size(self):
        return self._spectrogram_display_size

    @spectrogram_display_size.setter
    def spectrogram_display_size(self, new_value):
        self._spectrogram_display_size = max(1, new_value)
        self._slider_step_size = max(1, new_value / 20)
        self.slider_step_size_changed.emit(self._slider_step_size)

    def slider_step_size(self):
        return self._slider_step_size

    # @property
    # def annotations(self):
    #     return self._annotations

    # @annotations.setter
    # def annotations(self, annotations):
    #     pass
    # annotation_list = []
    # for annotation in annotations:
    #     annotation_list.append([
    #         annotation.time_start,
    #         annotation.time_end,
    #         annotation.freq_start,
    #         annotation.freq_end,
    #         annotation.label])
    # self.annotation_table_model._annotations = annotation_list
    # self.annotation_table_model.tableView.reloadData()
    # self._annotations = annotations
    # self.annotations_info_signal.emit(
    #     (self.annotations_column_names, self.annotations))

    # def annotations_changed(self):
    #     self.annotations_info_signal.emit(
    #         (self.annotations_column_names, self.annotations))

    @property
    def annotation_table_model(self):
        return self._annotation_table_model

    @annotation_table_model.setter
    def annotation_table_model(self, annotation_table_model):
        self._annotation_table_model = annotation_table_model

    @property
    def visible_annotations(self):
        return self._visible_annotations

    @visible_annotations.setter
    def visible_annotations(self, visible_annotations):
        self._visible_annotations = visible_annotations
        self.signal_visible_annotations()

    def signal_visible_annotations(self):
        times = self.spectrogram_data.times
        freqs = self.spectrogram_data.freqs
        display_start = self.current_spectrogram_chunk_data.times[0]
        self.visible_annotations_changed.emit(
            (self._visible_annotations, times, display_start, freqs))

    def update_visible_annotations(self, new_visible_annotations):
        self._visible_annotations += new_visible_annotations
        self.signal_visible_annotations()

    # def signal_annotation_field_change(self, value, row_id, column_id):
    #     self.annotation_field_changed.emit((row_id, column_id, value))

    def _value_to_dict(self, name, value):
        if isinstance(getattr(self, name), SerializableModel):
            return value.to_dict()
        else:
            return value

    def _value_from_dict(self, name, value):
        if name == "annotation_table_model":
            annotation_table_model = AnnotationTableModel(self)
            annotation_table_model.from_dict(value)
            return annotation_table_model
        else:
            return value

    # def emit_all_setting_signals(self):
    #     self.annotations_info_signal.emit(
    #         (self.annotations_column_names, self.annotations))


class ApplicationModel(QObject):
    """Application Model class.

    Keeps app configuration (app name, projects' paths, etc.).
    Keeps references to `MainWindow`s to prevent them from closing.
    """

    # signals
    text_warning_signal = Signal(str)

    def __init__(self):
        """Init model and load configuration from a file if it exists."""
        super().__init__()
        self.active_windows = set()
        self.background_tasks: Set[BackgroundTask] = set()
        self.app_name = "MoUSE"
        self.app_data_dir = Path(appdirs.user_data_dir(appname=self.app_name))
        self.app_config_dir = Path(appdirs.user_config_dir(appname=self.app_name))
        self.app_config_file = self.app_config_dir.joinpath("config.ini")
        self.user_projects: Set[MouseProject] = set()
        self.recent_project: Optional[MouseProject] = None
        self.min_time_between_warnings: datetime.timedelta = datetime.timedelta(
            seconds=1)
        self.warning_to_time: Dict[str, datetime.datetime] = dict()

        if self.app_config_file.exists():
            logging.debug("[ApplicationModel] Reading config file...")
            parser = configparser.ConfigParser()
            parser.read(self.app_config_file)
            user_projects = parser.get(section="CONFIGURATION",
                                       option="user_projects",
                                       fallback=str(set()))
            logging.debug(f"[ApplicationModel] Loaded projects: {user_projects}")
            self.user_projects = {
                MouseProject.from_string(entry) for entry in eval(user_projects)
            }

            recrent_project_string = parser.get(section="CONFIGURATION",
                                                option="last_project",
                                                fallback="")
            logging.debug(f"[ApplicationModel] Recent project: {user_projects}")
            if recrent_project_string != "":
                self.recent_project = MouseProject.from_string(recrent_project_string)

    def text_warning(self, warning):
        self.text_warning_signal.emit(warning)


class MainModel(NamedTuple):
    """Main Model class."""

    application_model: ApplicationModel
    project_model: Optional[ProjectModel]
    spectrogram_model: Optional[SpectrogramModel]
    settings_model: Optional[SettingsModel]

    def to_dict(self):
        all_models = {}
        for model in self:
            if isinstance(model, SerializableModel):
                all_models[model.__class__.__name__] = model.to_dict()

        return all_models

    def from_dict(self, model_dict):
        for model in self:
            if isinstance(model, SerializableModel):
                model.from_dict(model_dict[model.__class__.__name__])
