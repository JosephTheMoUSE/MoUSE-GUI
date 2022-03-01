from mouseapp.controller.utils import float_convert
from mouseapp.model.main_models import MainModel


def set_preview_start(model: MainModel, value: str):
    f_value = float_convert(value)
    model.settings_model.preview_start = f_value


def set_preview_end(model: MainModel, value: str):
    f_value = float_convert(value)
    model.settings_model.preview_end = f_value


def set_chosen_denoising_method(model: MainModel, value: str):
    model.settings_model.chosen_denoising_method = value


def emit_settings_signals(model: MainModel):
    model.settings_model.emit_all_setting_signals()
