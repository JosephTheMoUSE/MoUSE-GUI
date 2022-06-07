from pathlib import Path

import appdirs
from PySide6.QtCore import Signal

from mouse.classifier.cnn_classifier import PRETRAINED_MODELS_CHECKPOINTS
from mouseapp.model.utils import SerializableModel


class FilteringModel(SerializableModel):

    frequency_filter_changed = Signal(bool)
    frequency_threshold_changed = Signal(float)

    neural_network_filter_changed = Signal(bool)
    model_name_changed = Signal(str)
    model_batch_size_changed = Signal(int)
    model_confidence_threshold_changed = Signal(float)

    def __init__(self):
        super().__init__()

        self._default_values = {
            "_frequency_filter":
                False,
            "_frequency_threshold":
                18000.0,
            "_neural_network_filter":
                False,
            "_model_name":
                "cnn-binary-v1-custom",
            "_batch_size":
                1,
            "_confidence_threshold":
                0.2,
            "_cache_dir":
                Path(appdirs.user_data_dir(appname="MoUSE")) /
                "nn_pretrained_models_cache",
        }
        # Frequency filtering
        self._frequency_filter: bool = False
        self._frequency_threshold: float = 0.0

        # Neural network filtering
        self._neural_network_filter: bool = False
        self._model_name = "cnn-binary-v1-custom"
        self._batch_size = 1
        self._confidence_threshold = 0.2
        self._cache_dir = None

        self.set_default_values()
        self.emit_all_setting_signals()

    def set_default_values(self):
        for key, val in self._default_values.items():
            setattr(self, key, val)

    @property
    def frequency_filter(self) -> bool:
        return self._frequency_filter

    @frequency_filter.setter
    def frequency_filter(self, value: bool):
        self._frequency_filter = value

    @property
    def frequency_threshold(self) -> float:
        return self._frequency_threshold

    @frequency_threshold.setter
    def frequency_threshold(self, value: float):
        self._frequency_threshold = value

    @property
    def neural_network_filter(self) -> bool:
        return self._neural_network_filter

    @neural_network_filter.setter
    def neural_network_filter(self, value: bool):
        self._neural_network_filter = value

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        if value not in PRETRAINED_MODELS_CHECKPOINTS:
            raise ValueError(f"Model type should be one of "
                             f"{list(PRETRAINED_MODELS_CHECKPOINTS.keys())} "
                             f"but found {value}")
        self._model_name = value

    @property
    def batch_size(self):
        return int(self._batch_size)

    @batch_size.setter
    def batch_size(self, value: int):
        if value <= 0:
            raise ValueError("Batch size should be greater than zero")
        self._batch_size = int(value)

    @property
    def confidence_threshold(self):
        return self._confidence_threshold

    @confidence_threshold.setter
    def confidence_threshold(self, value: float):
        if value < 0:
            raise ValueError("Confidence threshold should be in range [0, 1]")
        self._confidence_threshold = value

    @property
    def cache_dir(self):
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, value: str):
        self._cache_dir = value

    def emit_all_setting_signals(self):
        self.frequency_filter_changed.emit(self.frequency_filter)
        self.frequency_threshold_changed.emit(self.frequency_threshold)

        self.neural_network_filter_changed.emit(self.neural_network_filter)
        self.model_name_changed.emit(self.model_name)
        self.model_batch_size_changed.emit(self.batch_size)
        self.model_confidence_threshold_changed.emit(self.confidence_threshold)

    def get_kwargs(self):
        kwargs = dict()
        for key in self._default_values.keys():
            value = getattr(self, key)
            kwargs[key[1:]] = value

        return kwargs

    def _value_to_dict(self, name, value):
        return value

    def _value_from_dict(self, name, value):
        return value
