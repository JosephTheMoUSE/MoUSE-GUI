import logging
from typing import Callable

import numpy as np
from mouse import segmentation
from mouse.nn_detection import neural_network
from mouse.utils.sound_util import SpectrogramData
from mouseapp.controller.denoising_controller import apply_denoising
from mouseapp.controller.main_controller import set_visible_annotations
from mouseapp.controller.utils import process_qt_events, run_background_task, warn_user
from mouseapp.model import constants
from mouseapp.model.main_models import MainModel
from mouseapp.model.settings.utils import Denoising, Detection
from mouseapp.model.utils import Annotation


def set_detection_method(model: MainModel, detection_method: Detection):
    model.settings_model.chosen_detection_method = detection_method


def _run_GAC(model: MainModel, callback: Callable, spectrogram: SpectrogramData):
    try:
        kwargs = model.settings_model.gac_model.get_kwargs()
        print("GAC detection starts with kwargs:", kwargs)

        # Set and update progress info
        model.spectrogram_model.progressbar_exists = True
        model.spectrogram_model.progressbar_primary_text = "GAC progress:"
        model.spectrogram_model.progressbar_count = 0
        model.spectrogram_model.progressbar_secondary_text = None

        def iter_callback(level_set: np.ndarray):
            num_progress = model.spectrogram_model.progressbar_count
            model.spectrogram_model.progressbar_progress = int(
                num_progress / kwargs["num_iter"] * 100)
            if num_progress == kwargs["num_iter"]:
                model.spectrogram_model.progressbar_progress = None
                model.spectrogram_model.progressbar_secondary_text = (
                    "level set to USVs conversion...")

            model.spectrogram_model.progressbar_count += 1

            callback(level_set)

        detections = segmentation.find_USVs(spectrogram,
                                            iter_callback=iter_callback,
                                            **kwargs)
        print("GAC detections:", detections)

        if model.settings_model.chosen_denoising_method == Denoising.BILATERAL:
            denoising_str = str(model.settings_model.bilateral_model)
        elif model.settings_model.chosen_denoising_method == Denoising.SDTS:
            denoising_str = str(model.settings_model.sdts_model)
        elif model.settings_model.chosen_denoising_method == Denoising.NOISE_GATE:
            denoising_str = str(model.settings_model.noise_gate_model)
        else:
            denoising_str = ""

        detection_str = str(model.settings_model.gac_model)

        method_str = denoising_str + detection_str
        annotations = list(
            map(
                lambda box: Annotation.from_squeak_box(
                    box,
                    spec_data=spectrogram,
                    table_data={constants.COL_DETECTION_METHOD: method_str},
                ),
                detections,
            ))
        model.spectrogram_model.annotation_table_model.append_annotations(annotations)
    finally:
        model.spectrogram_model.progressbar_exists = None
        model.spectrogram_model.progressbar_primary_text = None
        model.spectrogram_model.progressbar_count = None
        model.spectrogram_model.progressbar_secondary_text = None
        model.spectrogram_model.background_task = None


def _run_NN(model: MainModel, callback: Callable, spectrogram: SpectrogramData):
    try:
        model.spectrogram_model.progressbar_exists = True
        model.spectrogram_model.progressbar_primary_text = "NN progress:"
        model.spectrogram_model.progressbar_count = 0
        model.spectrogram_model.progressbar_secondary_text = None

        def _iter_callback(idx, total):
            num_progress = idx + 1
            model.spectrogram_model.progressbar_progress = int(num_progress / total *
                                                               100)
            if num_progress == total:
                model.spectrogram_model.progressbar_progress = None
                model.spectrogram_model.progressbar_secondary_text = "Merging boxes..."
            callback(None)

        detections = neural_network.find_USVs(
            spectrogram,
            **model.settings_model.nn_model.get_kwargs(),
            silent=True,
            callback=_iter_callback)

        if model.settings_model.chosen_denoising_method == Denoising.BILATERAL:
            denoising_str = str(model.settings_model.bilateral_model)
        elif model.settings_model.chosen_denoising_method == Denoising.SDTS:
            denoising_str = str(model.settings_model.sdts_model)
        elif model.settings_model.chosen_denoising_method == Denoising.NOISE_GATE:
            denoising_str = str(model.settings_model.noise_gate_model)
        else:
            denoising_str = ""

        detection_str = str(model.settings_model.nn_model)

        method_str = denoising_str + detection_str
        annotations = list(
            map(
                lambda box: Annotation.from_squeak_box(
                    box,
                    spec_data=spectrogram,
                    table_data={constants.COL_DETECTION_METHOD: method_str},
                ),
                detections,
            ))
        model.spectrogram_model.annotation_table_model.append_annotations(annotations)
    finally:
        model.spectrogram_model.progressbar_exists = None
        model.spectrogram_model.progressbar_primary_text = None
        model.spectrogram_model.progressbar_count = None
        model.spectrogram_model.progressbar_secondary_text = None
        model.spectrogram_model.background_task = None


def run_detection(model: MainModel, spectrogram: SpectrogramData):

    def _callback(_):
        process_qt_events(model.spectrogram_model.background_task.worker)

    if model.settings_model.chosen_detection_method == Detection.GAC:
        _run_GAC(model=model, callback=_callback, spectrogram=spectrogram)
    elif model.settings_model.chosen_detection_method == Detection.NN:
        _run_NN(model=model, callback=_callback, spectrogram=spectrogram)


def process_spectrogram(model: MainModel):
    detection_mutex = model.spectrogram_model.main_spectrogram_mutex
    logging.debug("Trying to acquire detection mutex...")
    if detection_mutex.tryLock():
        logging.debug("Detection mutex acquired.")
        model.spectrogram_model.detection_allowed = False
        model.spectrogram_model.classification_allowed = False
        model.spectrogram_model.filtering_allowed = False

        def _process_spectrogram():
            try:
                spectrogram = model.spectrogram_model.spectrogram_data
                if spectrogram is None:
                    warn_user(model, "There is no audio to run detection on!")
                    return

                chosen_denoising = model.settings_model.chosen_denoising_method
                if chosen_denoising != Denoising.NO_FILTER:
                    denoised_spectrogram = apply_denoising(model, spectrogram)
                else:
                    denoised_spectrogram = spectrogram

                run_detection(model, denoised_spectrogram)
            finally:
                model.spectrogram_model.detection_allowed = True
                model.spectrogram_model.classification_allowed = True
                model.spectrogram_model.filtering_allowed = True
                detection_mutex.unlock()
                set_visible_annotations(model)

        task = run_background_task(main_model=model,
                                   task=_process_spectrogram,
                                   can_be_stopped=True)
        model.spectrogram_model.background_task = task
