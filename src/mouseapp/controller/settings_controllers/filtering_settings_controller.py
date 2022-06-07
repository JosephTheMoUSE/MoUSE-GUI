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


def set_neural_network_filter(model: MainModel, value: bool):
    model.settings_model.filtering_model.neural_network_filter = value


def set_model_name(model: MainModel, model_name: str):
    model.settings_model.filtering_model.model_name = model_name.lower()


def set_batch_size(model: MainModel, batch_size: int):
    model.settings_model.filtering_model.batch_size = int(batch_size)


def set_confidence_threshold(model: MainModel, confidence_threshold: int):
    model.settings_model.filtering_model.confidence_threshold = confidence_threshold / 100
