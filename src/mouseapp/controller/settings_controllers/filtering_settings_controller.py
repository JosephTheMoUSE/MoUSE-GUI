import logging

from mouseapp.controller.utils import float_convert
from mouseapp.model.main_models import MainModel


def set_frequency_threshold(model: MainModel, threshold_txt: str):
    try:
        threshold = float_convert(threshold_txt)
        model.settings_model.filtering_model.frequency_threshold = threshold
        logging.debug(f"Value of threshold was changed to `{threshold}`")
    except ValueError:
        logging.debug(f"Failed to set threshold. Provided value "
                      f"`{threshold_txt}` couldn't be converted to float.")
        model.settings_model.filtering_model.frequency_threshold_changed.emit(
            model.settings_model.filtering_model.frequency_threshold)


def set_frequency_filter(model: MainModel, value: bool):
    model.settings_model.filtering_model.frequency_filter = value
