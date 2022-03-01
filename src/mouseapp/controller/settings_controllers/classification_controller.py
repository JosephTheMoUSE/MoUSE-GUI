import logging

from mouseapp.controller.utils import float_convert
from mouseapp.model.main_models import MainModel


def set_frequency_threshold(model: MainModel, threshold_txt: str):
    try:
        threshold = float_convert(threshold_txt)
        model.settings_model.threshold_model.threshold = threshold
        logging.debug(f"Value of threshold was changed to `{threshold}`")
    except ValueError:
        logging.debug(f"Failed to set threshold. Provided value "
                      f"`{threshold_txt}` couldn't be converted to float.")


def set_low_freq_label(model: MainModel, label: str):
    model.settings_model.threshold_model.label_low = label
    logging.debug(f"Value of low frequency label was changed to `{label}`")


def set_high_freq_label(model: MainModel, label: str):
    model.settings_model.threshold_model.label_high = label
    logging.debug(f"Value of high frequency label was changed to `{label}`")
