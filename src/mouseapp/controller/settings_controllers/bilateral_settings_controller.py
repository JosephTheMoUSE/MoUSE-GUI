import time

from mouse.utils.sound_util import clip_spectrogram
from mouseapp.controller import denoising_controller
from mouseapp.controller.utils import run_background_task, float_convert
from mouseapp.model.main_models import MainModel


def set_d(model: MainModel, value: int):
    model.settings_model.bilateral_model.d = value


def set_sigma_color(model: MainModel, value: str):
    f_value = float_convert(value)
    model.settings_model.bilateral_model.sigma_color = f_value


def set_sigma_space(model: MainModel, value: str):
    f_value = float_convert(value)
    model.settings_model.bilateral_model.sigma_space = f_value


def restore_default_bilateral_values(model: MainModel):
    model.settings_model.bilateral_model.set_default_values()
    model.settings_model.bilateral_model.emit_all_setting_signals()


def emit_settings_signals(model: MainModel):
    model.settings_model.bilateral_model.emit_all_setting_signals()


def set_bilateral_preview(model: MainModel):
    bilateral_model = model.settings_model.bilateral_model
    inital_mutex = bilateral_model.preview_model.initial_mutex
    calculation_mutex = bilateral_model.preview_model.calculation_mutex

    def set_preview():
        # prevent too frequent updates
        time.sleep(bilateral_model.preview_model.time_between_updates)

        calculation_mutex.lock()
        inital_mutex.unlock()

        spec = model.spectrogram_model.spectrogram_data
        t_start = model.settings_model.preview_start
        t_end = model.settings_model.preview_end
        orginal_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)
        model.settings_model.denoising_spectrogram_data = orginal_spec

        preview_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)

        denoising_controller.apply_bilateral_filter(model, preview_spec)

        bilateral_model.preview_model.preview_data = preview_spec

        calculation_mutex.unlock()

    if inital_mutex.tryLock():
        run_background_task(main_model=model, task=set_preview, can_be_stopped=False)
