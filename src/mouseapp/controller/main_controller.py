"""Main Controller of the application.

Only functions related to `MainWindow`, `SpectrogramTab` and `ProjectTab`
should be kept here, unless a specialized file is already exists. Those files
include: `detection_controller.py`.
"""
import os
from collections import defaultdict
from pathlib import Path
from typing import Union, Optional, List

import numpy as np
import pandas as pd
import torch
import torchaudio
from PySide6 import QtCore
from mouse.utils import sound_util
from mouseapp.controller.utils import warn_user, float_convert
from mouseapp.model import constants
from mouseapp.model.main_models import MainModel
from mouseapp.model.utils import Annotation


def set_project_name(model: MainModel, name: str):
    model.project_model.project_name = name


def set_experiment_date(model: MainModel, date: QtCore.QDate):
    model.project_model.experiment_date = date


def set_project_note(model: MainModel, note: str):
    model.project_model.experiment_note = note


def add_key_value_metadata(model: MainModel, key_value: tuple, value_type: str):
    type_map = {
        "Text":
            str,
        "Integer":
            lambda x: x
            if type(x) == str and len(x) == 0 else int(float_convert(str(x))),
        "Real":
            lambda x: x if type(x) == str and len(x) == 0 else float_convert(str(x)),
    }

    if len(key_value[0]) == 0:
        warn_user(model, "Key cannot be empty")
        return

    if key_value[0] in model.project_model.project_metadata:
        warn_user(model, "Metadata with given key already exists")
        return

    try:
        key_value_casted = (
            key_value[0],
            type_map[value_type](key_value[1]),
            value_type,
        )
    except ValueError:
        warn_user(model, f"Cannot interpret {key_value[1]} as {value_type}")
        return

    model.project_model.add_project_metadata(key_value_casted)


def update_key_value_metadata(model: MainModel,
                              key: str,
                              value: str = None,
                              vtype: str = None):
    value_type = model.project_model.project_metadata[key]
    if value is not None and value != str(value_type[0]):
        value_type = (value, value_type[1])
    elif vtype is not None and vtype != value_type[1]:
        value_type = (value_type[0], vtype)
    else:
        return

    type_map = {
        "Text":
            str,
        "Integer":
            lambda x: x if type(x) in [str, np.str_] and len(x) == 0 else int(
                float_convert(str(x))),
        "Real":
            lambda x: x
            if type(x) in [str, np.str_] and len(x) == 0 else float_convert(str(x)),
    }

    try:
        key_value_casted = (key, type_map[value_type[1]](value_type[0]), value_type[1])
    except ValueError:
        warn_user(model, f"Cannot interpret {value_type[0]} as {value_type[1]}")
        value_type = model.project_model.project_metadata[key]
        key_value_casted = (key, value_type[0], value_type[1])

    model.project_model.update_project_metadata(key_value_casted)


def remove_key_value_metadata(model: MainModel, key: Union[str, int, float]):
    model.project_model.remove_project_metadata(key)


def load_audio_files(model: MainModel, files: Union[str, list], folder=False):
    """Load and sort audio files to the project."""
    if folder:
        audio_files = [
            Path(root, name)
            for (root, dirs, file_names) in os.walk(files)
            for name in file_names
            if name.endswith((".wav", ".mp3"))
        ]
    else:
        audio_files = [Path(file) for file in files]
    audio_files.sort()
    model.project_model.audio_files = audio_files


def _generate_spectrogram(model: MainModel, signal_data: Optional[torch.Tensor]):
    spectrogram_model = model.spectrogram_model
    if spectrogram_model.spectrogram_calculator is None:
        spectrogram_calculator = torchaudio.transforms.Spectrogram(
            n_fft=spectrogram_model.n_fft,
            win_length=spectrogram_model.win_length,
            hop_length=spectrogram_model.hop_length,
            center=spectrogram_model.center,
            pad_mode=spectrogram_model.pad_mode,
            power=spectrogram_model.power,
        )
        spectrogram_model.spectrogram_calculator = spectrogram_calculator

    if signal_data is not None:
        spectrogram_data = sound_util.spectrogram(
            signal_data,
            sample_rate=spectrogram_model.sample_rate,
            spec_calculator=spectrogram_model.spectrogram_calculator,
            n_fft=spectrogram_model.n_fft,
            win_length=spectrogram_model.win_length,
            hop_length=spectrogram_model.hop_length,
            power=spectrogram_model.power,
        )
    else:
        spectrogram_data = None
    spectrogram_model.spectrogram_data = spectrogram_data


def update_signal_data(model: MainModel, audio_files: List[Path]):
    signal_data = []
    cur_sample_rate = None
    spectrogram_model = model.spectrogram_model
    for file in audio_files:
        waveform, sample_rate = torchaudio.load(file)
        if cur_sample_rate is not None:
            if cur_sample_rate != sample_rate:
                # TODO(#71): resample audio files to lowest sample rate
                warn_user(
                    model,
                    "Files have different sample rate which may"
                    " lead to unexpected behavior! 😠",
                )
        else:
            cur_sample_rate = sample_rate
        signal_data.append(waveform.squeeze())
    if len(signal_data) > 0:
        signal_data = torch.cat(signal_data)
    else:
        signal_data = None
    spectrogram_model.sample_rate = cur_sample_rate
    _generate_spectrogram(model, signal_data)


def _align_time_mask(prev_time_mask: np.ndarray, time_mask: np.ndarray):
    if prev_time_mask is None:
        return time_mask

    time_mask_size = np.sum(prev_time_mask)
    size = np.sum(time_mask)
    if size > time_mask_size:
        idx = time_mask.nonzero()[0][0]
        time_mask[idx:idx + (size - time_mask_size) + 1] = 0
    elif size < time_mask_size:
        idx = time_mask.nonzero()[0][-1]
        time_mask[idx:idx + (time_mask_size - size) + 1] = 1
    return time_mask


def _get_time_mask(model: MainModel, start_time: float, end_time: float):
    spectrogram_model = model.spectrogram_model
    spec_time = spectrogram_model.spectrogram_data.times
    time_mask = np.logical_and(spec_time >= start_time, spec_time <= end_time)
    time_mask = _align_time_mask(spectrogram_model.time_mask, time_mask)
    return time_mask


def _set_current_spectrogram_chunk(model: MainModel, start_time: float):
    spectrogram_model = model.spectrogram_model
    time_mask = _get_time_mask(
        model,
        start_time,
        start_time + spectrogram_model.spectrogram_display_size / 1000,
    )
    spectrogram_model.time_mask = time_mask
    current_spectrogram_chunk_data = sound_util.SpectrogramData(
        spec=spectrogram_model.spectrogram_data.spec[:, time_mask],
        times=spectrogram_model.spectrogram_data.times[time_mask],
        freqs=spectrogram_model.spectrogram_data.freqs,
    )
    spectrogram_model.current_spectrogram_chunk_data = current_spectrogram_chunk_data


def set_visible_annotations(model: MainModel):
    spectrogram_model = model.spectrogram_model
    visible_annotations = []
    (
        display_start_time,
        display_end_time,
    ) = spectrogram_model.current_spectrogram_chunk_data.times[[0, -1]]
    for annotation in spectrogram_model.annotation_table_model.annotations:
        if ((display_start_time <= annotation.time_start < display_end_time) or
            (display_start_time <= annotation.time_end < display_end_time) or
            (annotation.time_start <= display_start_time and
             display_end_time <= annotation.time_end)):
            visible_annotations.append(annotation)
    spectrogram_model.visible_annotations = visible_annotations


def update_from_slider_position(model: MainModel, position: int):
    _set_current_spectrogram_chunk(model, position / 1000)
    set_visible_annotations(model)


def remove_audio_file(model: MainModel, file_name: str):
    model.project_model.remove_audio_file(file_name)


def load_annotations(model: MainModel, filename: Path):
    required_colums = {
        constants.COL_BEGIN_TIME,
        constants.COL_END_TIME,
        constants.COL_LOW_FREQ,
        constants.COL_HIGH_FREQ,
        constants.COL_USV_LABEL,
    }

    annotations_df = pd.read_csv(filename, sep=None, engine="python", comment="#")
    if constants.COL_USV_LABEL not in annotations_df.columns:
        annotations_df.rename(columns={"NOTE": constants.COL_USV_LABEL}, inplace=True)

    if not required_colums.issubset(annotations_df.columns):
        warn_user(
            model,
            (
                "Loaded annotations file should have following collumns: ",
                f"{required_colums}",
            ),
        )
        return

    column_names = [
        column_name for column_name in annotations_df.columns
        if column_name not in required_colums
    ]
    column_names = [
        constants.COL_BEGIN_TIME,
        constants.COL_END_TIME,
        constants.COL_LOW_FREQ,
        constants.COL_HIGH_FREQ,
        constants.COL_USV_LABEL,
    ] + column_names

    model.spectrogram_model.annotation_table_model.update_annotations_column_names(
        column_names)
    annotations = []
    for _, entry in annotations_df.iterrows():
        table_data = {column_name: entry[column_name] for column_name in column_names}
        table_data = defaultdict(lambda: "", table_data)

        annotations.append(
            Annotation(
                time_start=entry[constants.COL_BEGIN_TIME],
                time_end=entry[constants.COL_END_TIME],
                freq_start=entry[constants.COL_LOW_FREQ],
                freq_end=entry[constants.COL_HIGH_FREQ],
                label=entry[constants.COL_USV_LABEL],
                table_data=table_data,
            ))

    model.spectrogram_model.annotation_table_model.append_annotations(annotations)
    set_visible_annotations(model)


def _handle_change_in_check_state(model: MainModel, new_check_state: bool, row_id: int):
    if new_check_state:
        model.spectrogram_model.annotation_table_model.checked_annotations_counter += 1
        model.spectrogram_model.annotation_table_model.annotations[
            row_id].checked = True
    else:
        model.spectrogram_model.annotation_table_model.checked_annotations_counter -= 1
        model.spectrogram_model.annotation_table_model.annotations[
            row_id].checked = False


def update_annotation(
    model: MainModel,
    annotation,
    time_pixel_start,
    freq_pixel_start,
    time_pixel_end,
    freq_pixel_end,
):
    offset = model.spectrogram_model.time_mask.nonzero()[0][0]
    time_pixel_start += offset
    time_pixel_end += offset

    spectrogram_data = model.spectrogram_model.spectrogram_data
    time_start, time_end = spectrogram_data.times[[time_pixel_start, time_pixel_end]]
    freq_start, freq_end = spectrogram_data.freqs[[freq_pixel_start, freq_pixel_end]]

    annotation.time_start = time_start
    annotation.time_end = time_end
    annotation.freq_start = freq_start
    annotation.freq_end = freq_end
    # todo(werkaaa): Can it be done more efficiently?
    model.spectrogram_model.annotation_table_model.update_all_displayed_data()


def add_new_annotation(model: MainModel,
                       time_pixel_start,
                       freq_pixel_start,
                       time_pixel_end,
                       freq_pixel_end):
    offset = model.spectrogram_model.time_mask.nonzero()[0][0]
    time_pixel_start += offset
    time_pixel_end += offset

    spectrogram_data = model.spectrogram_model.spectrogram_data
    time_start, time_end = spectrogram_data.times[[time_pixel_start, time_pixel_end]]
    freq_start, freq_end = spectrogram_data.freqs[[freq_pixel_start, freq_pixel_end]]
    table_data = {
        constants.COL_BEGIN_TIME: time_start,
        constants.COL_END_TIME: time_end,
        constants.COL_LOW_FREQ: freq_start,
        constants.COL_HIGH_FREQ: freq_end,
        constants.COL_USV_LABEL: "Unknown",
        constants.COL_DETECTION_METHOD: "Manual",
    }
    table_data = defaultdict(lambda: "", table_data)

    annotation = Annotation(
        time_start=time_start,
        time_end=time_end,
        freq_start=freq_start,
        freq_end=freq_end,
        label="Unknown",
        table_data=table_data,
    )
    model.spectrogram_model.update_visible_annotations([annotation])
    model.spectrogram_model.annotation_table_model.append_annotations([annotation])


def export_annotations(model: MainModel, filename: Path):
    annotations = model.spectrogram_model.annotation_table_model.annotations
    project_model = model.project_model

    # Get keys
    default_dict_key_set = set()
    for annotation in annotations:
        default_dict_key_set.update(annotation.table_data.keys())

    annotations_dict = {k: [] for k in default_dict_key_set}

    for annotation in annotations:
        for k in default_dict_key_set:
            annotations_dict[k].append(annotation.table_data[k])

    annotations_df = pd.DataFrame.from_dict(annotations_dict)

    columns_order = [
        constants.COL_BEGIN_TIME,
        constants.COL_END_TIME,
        constants.COL_LOW_FREQ,
        constants.COL_HIGH_FREQ,
        constants.COL_USV_LABEL,
    ]

    # Set proper columns order
    columns_order += list(default_dict_key_set - set(columns_order))
    annotations_df = annotations_df.reindex(columns=columns_order)

    with open(filename, "w") as f:
        f.write(f"# Project name: {project_model.project_name}\n")
        f.write(f"# Experiment date: {project_model.experiment_date}\n")
        f.write(f"# Note: {project_model.experiment_note}\n")
        for k, v in project_model.project_metadata.items():
            if v[1] == "Text":
                f.write(f'# {k}: "{v[0]}"\n')
            else:
                f.write(f"# {k}: {v[0]}\n")
        f.write(("# Audio files: "
                 f'{",".join([str(audio) for audio in project_model.audio_files])}'
                 "\n"))
        annotations_df.to_csv(f, index=False)
    print(f"Saved annotations to {filename}")


def delete_selected_annotations(model: MainModel):
    n = len(model.spectrogram_model.annotation_table_model.annotations)
    removed_annotations = set()
    for i, annotation in enumerate(
        model.spectrogram_model.annotation_table_model.annotations[::-1]
    ):
        id = n - i - 1
        if annotation.checked:
            model.spectrogram_model.annotation_table_model.removeRows(id)
            removed_annotations.add(annotation)

    # This will signal the spectrogram as well.
    model.spectrogram_model.visible_annotations = list(
        set(model.spectrogram_model.visible_annotations) - removed_annotations)

    if len(model.spectrogram_model.annotation_table_model.annotations) == 0:
        model.spectrogram_model.annotations_column_names = [
            constants.COL_BEGIN_TIME,
            constants.COL_END_TIME,
            constants.COL_LOW_FREQ,
            constants.COL_HIGH_FREQ,
            constants.COL_USV_LABEL,
            constants.COL_DETECTION_METHOD,
        ]

    model.spectrogram_model.annotation_table_model.checked_annotations_counter = 0


def delete_all_annotations(model: MainModel):
    model.spectrogram_model.annotation_table_model.annotations_column_names = [
        constants.COL_BEGIN_TIME,
        constants.COL_END_TIME,
        constants.COL_LOW_FREQ,
        constants.COL_HIGH_FREQ,
        constants.COL_USV_LABEL,
        constants.COL_DETECTION_METHOD,
    ]
    annotation_number = len(model.spectrogram_model.annotation_table_model.annotations)
    model.spectrogram_model.annotation_table_model.removeRows(0, annotation_number)
    model.spectrogram_model.visible_annotations = []
    model.spectrogram_model.annotation_table_model.checked_annotations_counter = 0


def filter_annotations(model: MainModel):
    annotations = model.spectrogram_model.annotation_table_model.annotations
    if model.settings_model.filtering_model.frequency_filter:
        threshold = model.settings_model.filtering_model.frequency_threshold
        for i, annotation in enumerate(annotations):
            if 0.5 * (annotation.freq_start + annotation.freq_end) <= threshold:
                model.spectrogram_model.annotation_table_model.check_annotation(i, True)
                model.spectrogram_model.annotation_table_model.update_selected_field(
                    i, 0)


def update_annotation_table_model(model: MainModel, view):
    """Create new annotation_table_model with new view."""
    saved_model = model.spectrogram_model.annotation_table_model
    model.spectrogram_model.annotation_table_model = saved_model.copy_with_view(view)
    saved_model.deleteLater()
    return model.spectrogram_model.annotation_table_model
