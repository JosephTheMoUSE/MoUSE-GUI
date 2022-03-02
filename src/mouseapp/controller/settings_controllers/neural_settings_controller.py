import time
import warnings
from typing import Callable

import mouseapp.controller.utils
from PySide6.QtCore import QMutex
from mouse.nn_detection.neural_network import find_USVs
from mouse.utils.sound_util import clip_spectrogram
from mouseapp.controller.settings_controllers.utils import set_denoising_for_detection
from mouseapp.controller.utils import run_background_task
from mouseapp.model.main_models import MainModel
from mouseapp.model.utils import BackgroundTask


def restore_default_nn_values(model: MainModel):
    model.settings_model.nn_model.set_default_values()
    model.settings_model.nn_model.emit_all_setting_signals()


def emit_settings_signals(model: MainModel):
    model.settings_model.nn_model.emit_all_setting_signals()


def set_model_name(model: MainModel, model_name: str):
    model.settings_model.nn_model.model_name = model_name.lower()


def set_batch_size(model: MainModel, batch_size: int):
    model.settings_model.nn_model.batch_size = int(batch_size)


def set_confidence_threshold(model: MainModel, confidence_threshold: int):
    model.settings_model.nn_model.confidence_threshold = confidence_threshold / 100


def set_NN_preview(model: MainModel):
    nn_model = model.settings_model.nn_model
    inital_mutex = nn_model.preview_model.initial_mutex
    calculation_mutex = nn_model.preview_model.calculation_mutex

    def set_preview():
        # prevent too frequent updates
        model.settings_model.nn_model.preview_model.is_method_allowed = False
        time.sleep(nn_model.preview_model.time_between_updates)

        calculation_mutex.lock()
        inital_mutex.unlock()

        spec = model.spectrogram_model.spectrogram_data
        t_start = model.settings_model.preview_start
        t_end = model.settings_model.preview_end

        original_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)
        set_denoising_for_detection(model, [original_spec])
        model.settings_model.detection_spectrogram_data = original_spec

        nn_model.preview_model.preview_data = original_spec

        nn_model.preview_model.is_method_allowed = True
        calculation_mutex.unlock()

    if inital_mutex.tryLock():
        run_background_task(main_model=model, task=set_preview, can_be_stopped=False)


def _run_preview_NN(model: MainModel, calculation_mutex: QMutex, callback: Callable):
    try:
        preview_model = model.settings_model.nn_model.preview_model

        preview_model.is_method_allowed = False
        spec = model.settings_model.detection_spectrogram_data

        def _iter_callback(idx, total):
            callback()

        detections = find_USVs(spec,
                               **model.settings_model.nn_model.get_kwargs(),
                               silent=True,
                               callback=_iter_callback)

        preview_model.detections = detections
    finally:
        calculation_mutex.unlock()
        model.settings_model.nn_model.preview_model.is_method_allowed = True


def run_preview_NN(model: MainModel):
    calculation_mutex = model.settings_model.nn_model.preview_model.calculation_mutex

    if calculation_mutex.tryLock():

        def _callback():
            receiver = (
                model.settings_model.nn_model.preview_model.calculation_task.worker)
            mouseapp.controller.utils.process_qt_events(receiver=receiver)

        task = run_background_task(
            main_model=model,
            task=_run_preview_NN,
            can_be_stopped=True,
            model=model,
            calculation_mutex=calculation_mutex,
            callback=_callback,
        )
        model.settings_model.nn_model.preview_model.calculation_task = task


def stop_nn(model: MainModel):
    preview_model = model.settings_model.nn_model.preview_model
    if isinstance(preview_model.calculation_task, BackgroundTask):
        if not preview_model.calculation_task.is_killable():
            warnings.warn("Trying to kill a task which can't be killed!")
            return
        preview_model.calculation_task.kill()
