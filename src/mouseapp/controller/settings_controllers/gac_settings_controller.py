import time
import warnings
from typing import Callable

import mouseapp.controller.utils
import torch
from PySide6.QtCore import QMutex
from mouse import segmentation
from mouse.utils.sound_util import clip_spectrogram, SpectrogramData
from mouseapp.controller.settings_controllers.utils import set_denoising_for_detection
from mouseapp.controller.utils import warn_user, run_background_task, float_convert
from mouseapp.model.main_models import MainModel
from mouseapp.model.utils import BackgroundTask


def set_baloon(model: MainModel, value: str):
    text_to_number = {"positive": 1.0, "none": 0, "negative": -1}
    model.settings_model.gac_model.balloon = text_to_number[value.lower()]


def set_threshold(model: MainModel, value: float):
    if not (0 <= value <= 1):
        warn_user(model=model, message="Threshold must be between 0 and 1!")
    else:
        model.settings_model.gac_model.threshold = value


def set_iterations(model: MainModel, value: int):
    if 0 >= value:
        warn_user(model=model, message="Iterations must be positive!")
    else:
        model.settings_model.gac_model.iterations = value


def set_smoothing(model: MainModel, value: int):
    model.settings_model.gac_model.smoothing = value


def set_alpha(model: MainModel, value: str):
    f_value = float_convert(value)
    model.settings_model.gac_model.alpha = f_value


def set_sigma(model: MainModel, value: float):
    f_value = float_convert(value)
    model.settings_model.gac_model.sigma = f_value


def set_flood_threshold(model: MainModel, value: float):
    model.settings_model.gac_model.flood_threshold = value


def restore_default_gac_values(model: MainModel):
    model.settings_model.gac_model.set_default_values()
    model.settings_model.gac_model.emit_all_setting_signals()


def emit_settings_signals(model: MainModel):
    model.settings_model.gac_model.emit_all_setting_signals()


def set_gac_preview(model: MainModel):
    gac_model = model.settings_model.gac_model
    inital_mutex = gac_model.preview_model.initial_mutex
    calculation_mutex = gac_model.preview_model.calculation_mutex

    def set_preview():
        # prevent too frequent updates
        model.settings_model.gac_model.preview_model.is_gac_allowed = False
        time.sleep(gac_model.preview_model.time_between_updates)

        calculation_mutex.lock()
        model.settings_model.gac_model.preview_model.is_gac_allowed = False
        inital_mutex.unlock()

        spec = model.spectrogram_model.spectrogram_data
        t_start = model.settings_model.preview_start
        t_end = model.settings_model.preview_end
        clipped_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)
        original_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)
        set_denoising_for_detection(model, [clipped_spec, original_spec])
        model.settings_model.detection_spectrogram_data = original_spec

        clipped_spec.spec = torch.Tensor(gac_model.get_kwargs()["preprocessing_fn"](
            clipped_spec.spec.numpy()))

        init_level_set = gac_model.get_kwargs()["level_set"](clipped_spec.spec.numpy())
        gac_model.preview_model.initial_level_set = init_level_set

        gac_model.preview_model.preview_data = clipped_spec

        model.settings_model.gac_model.preview_model.is_gac_allowed = True
        calculation_mutex.unlock()

    if inital_mutex.tryLock():
        run_background_task(main_model=model, task=set_preview, can_be_stopped=False)


def _run_preview_GAC(model: MainModel, calculation_mutex: QMutex, callback: Callable):
    try:
        preview_model = model.settings_model.gac_model.preview_model

        preview_model.is_gac_allowed = False
        preview_model.initial_level_set = None
        kwargs = model.settings_model.gac_model.get_kwargs()
        print("GAC detection starts with kwargs:", kwargs)
        spec = model.settings_model.detection_spectrogram_data

        preview_model.last_gac_step = time.time() - preview_model.time_between_gac_steps

        def _iter_callback(level_set):
            delta_time = time.time() - preview_model.last_gac_step
            sleep_time = max(0, preview_model.time_between_gac_steps - delta_time)
            time.sleep(sleep_time)
            level_set_spec = SpectrogramData(spec=torch.Tensor(level_set),
                                             times=spec.times,
                                             freqs=spec.freqs)
            preview_model.preview_data = level_set_spec
            preview_model.last_gac_step = time.time()

            callback()

        detections = segmentation.find_USVs(spec,
                                            iter_callback=_iter_callback,
                                            **kwargs)
        print("GAC detections:", detections)

        preview_model.detections = detections
    finally:
        calculation_mutex.unlock()
        model.settings_model.gac_model.preview_model.is_gac_allowed = True


def run_preview_GAC(model: MainModel):
    calculation_mutex = model.settings_model.gac_model.preview_model.calculation_mutex

    if calculation_mutex.tryLock():

        def _callback():
            receiver = (
                model.settings_model.gac_model.preview_model.calculation_task.worker)
            mouseapp.controller.utils.process_qt_events(receiver=receiver)

        task = run_background_task(
            main_model=model,
            task=_run_preview_GAC,
            can_be_stopped=True,
            model=model,
            calculation_mutex=calculation_mutex,
            callback=_callback,
        )
        model.settings_model.gac_model.preview_model.calculation_task = task


def stop_gac(model: MainModel):
    preview_model = model.settings_model.gac_model.preview_model
    if isinstance(preview_model.calculation_task, BackgroundTask):
        if not preview_model.calculation_task.is_killable():
            warnings.warn("Trying to kill a task which can't be killed!")
            return
        preview_model.calculation_task.kill()


def emit_detections(model: MainModel):
    model.settings_model.gac_model.preview_model.detections = (
        model.settings_model.gac_model.preview_model.detections)
