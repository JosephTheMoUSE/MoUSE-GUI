import time

from mouse.utils.sound_util import clip_spectrogram
from mouseapp.controller import denoising_controller
from mouseapp.controller.utils import run_background_task
from mouseapp.model.main_models import MainModel


def set_noise_decrease(model: MainModel, value: float):
    model.settings_model.sdts_model.noise_decrease = value


def set_m(model: MainModel, value: int):
    model.settings_model.sdts_model.m = value


def restore_default_sdts_values(model: MainModel):
    model.settings_model.sdts_model.set_default_values()
    model.settings_model.sdts_model.emit_all_setting_signals()


def emit_settings_signals(model: MainModel):
    model.settings_model.sdts_model.emit_all_setting_signals()


def set_sdts_preview(model: MainModel):
    sdts_model = model.settings_model.sdts_model
    inital_mutex = sdts_model.preview_model.initial_mutex
    calculation_mutex = sdts_model.preview_model.calculation_mutex

    def set_preview():
        # prevent too frequent updates
        time.sleep(sdts_model.preview_model.time_between_updates)

        calculation_mutex.lock()
        inital_mutex.unlock()

        spec = model.spectrogram_model.spectrogram_data
        t_start = model.settings_model.preview_start
        t_end = model.settings_model.preview_end
        orginal_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)
        model.settings_model.denoising_spectrogram_data = orginal_spec

        preview_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)
        denoising_controller.apply_sdts_filter(model, preview_spec)

        sdts_model.preview_model.preview_data = preview_spec

        calculation_mutex.unlock()

    if inital_mutex.tryLock():
        run_background_task(main_model=model, task=set_preview, can_be_stopped=False)
