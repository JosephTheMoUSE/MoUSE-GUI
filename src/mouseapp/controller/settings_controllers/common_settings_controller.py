from mouseapp.controller.utils import float_convert, warn_user
from mouseapp.model.main_models import MainModel


def set_preview_start_end(model: MainModel, prev_start: str, prev_end: str):
    f_prev_start = float_convert(prev_start)
    f_prev_end = float_convert(prev_end)
    if f_prev_start < f_prev_end:
        model.settings_model.preview_start = f_prev_start
        model.settings_model.preview_end = f_prev_end
        return True
    else:
        warn_user(model, message="Preview start must be before preview end")
        return False


def set_chosen_denoising_method(model: MainModel, value: str):
    model.settings_model.chosen_denoising_method = value


def emit_settings_signals(model: MainModel):
    model.settings_model.emit_all_setting_signals()
