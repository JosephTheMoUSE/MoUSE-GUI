from typing import Optional

from PySide6.QtCore import Signal
from mouse.utils.sound_util import SpectrogramData
from mouseapp.model.settings.classification_models import ThresholdModel
from mouseapp.model.settings.denoising_models import (NoFilterModel,
                                                      BilateralModel,
                                                      SDTSModel,
                                                      NoiseGateModel)
from mouseapp.model.settings.filtering_model import FilteringModel
from mouseapp.model.settings.detection_models import GACModel, NNModel
from mouseapp.model.settings.utils import Denoising, Detection
from mouseapp.model.utils import SerializableModel


class SettingsModel(SerializableModel):
    time_start_changed = Signal(float)
    time_end_changed = Signal(float)
    denoising_spec_changed = Signal(SpectrogramData)
    detection_spec_changed = Signal(SpectrogramData)
    chosen_denoising_method_signal = Signal(str)
    chosen_detection_method_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._denoising_spectrogram_data: Optional[SpectrogramData] = None
        self._detection_spectrogram_data: Optional[SpectrogramData] = None
        self._preview_start: Optional[float] = 0.
        self._preview_end: Optional[float] = 1.

        self._chosen_denoising_method = Denoising.NO_FILTER
        self._chosen_detection_method = Detection.GAC

        # Denoising model
        self._no_filter_model = NoFilterModel()
        self._bilateral_model = BilateralModel()
        self._sdts_model = SDTSModel()
        self._noise_gate_model = NoiseGateModel()

        # Detection models
        self._gac_model = GACModel()
        self._nn_model = NNModel()

        # Filtering model
        self._filtering_model = FilteringModel()

        # Classification models
        self._threshold_model = ThresholdModel()

        self._dict_denylist.update([
            'no_filter_model',
            'denoising_spectrogram_data',
            'detection_spectrogram_data',
        ])

    @property
    def preview_start(self):
        return self._preview_start

    @preview_start.setter
    def preview_start(self, value):
        self.time_start_changed.emit(value)
        self._preview_start = value

    @property
    def preview_end(self):
        return self._preview_end

    @preview_end.setter
    def preview_end(self, value: float):
        self.time_end_changed.emit(value)
        self._preview_end = value

    @property
    def chosen_denoising_method(self):
        return self._chosen_denoising_method

    @chosen_denoising_method.setter
    def chosen_denoising_method(self, value: str):
        self._chosen_denoising_method = value

    @property
    def chosen_detection_method(self):
        return self._chosen_detection_method

    @chosen_detection_method.setter
    def chosen_detection_method(self, value: Detection):
        self._chosen_detection_method = value

    @property
    def denoising_spectrogram_data(self):
        return self._denoising_spectrogram_data

    @denoising_spectrogram_data.setter
    def denoising_spectrogram_data(self, value: float):
        self.denoising_spec_changed.emit(value)
        self._spectrogram_data = value

    @property
    def detection_spectrogram_data(self):
        return self._detection_spectrogram_data

    @detection_spectrogram_data.setter
    def detection_spectrogram_data(self, value: float):
        self.detection_spec_changed.emit(value)
        self._detection_spectrogram_data = value

    @property
    def no_filter_model(self):
        return self._no_filter_model

    @no_filter_model.setter
    def no_filter_model(self, value):
        self._no_filter_model = value

    @property
    def bilateral_model(self):
        return self._bilateral_model

    @bilateral_model.setter
    def bilateral_model(self, value):
        self._bilateral_model = value

    @property
    def sdts_model(self):
        return self._sdts_model

    @sdts_model.setter
    def sdts_model(self, value):
        self._sdts_model = value

    @property
    def noise_gate_model(self):
        return self._noise_gate_model

    @noise_gate_model.setter
    def noise_gate_model(self, value):
        self._noise_gate_model = value

    @property
    def gac_model(self):
        return self._gac_model

    @gac_model.setter
    def gac_model(self, value):
        self._gac_model = value

    @property
    def nn_model(self) -> NNModel:
        return self._nn_model

    @nn_model.setter
    def nn_model(self, value: NNModel):
        self._nn_model = value

    @property
    def filtering_model(self) -> FilteringModel:
        return self._filtering_model

    @filtering_model.setter
    def filtering_model(self, value: FilteringModel):
        self._filtering_model = value

    @property
    def threshold_model(self) -> ThresholdModel:
        return self._threshold_model

    @threshold_model.setter
    def threshold_model(self, value: ThresholdModel):
        self._threshold_model = value

    def _value_to_dict(self, name, value):
        if isinstance(getattr(self, name), SerializableModel):
            return value.to_dict()
        else:
            return value

    def _value_from_dict(self, name, value):
        if name == "gac_model":
            gac_model = GACModel()
            gac_model.from_dict(value)
            return gac_model
        elif name == "bilateral_model":
            bilateral_model = BilateralModel()
            bilateral_model.from_dict(value)
            return bilateral_model
        elif name == "sdts_model":
            sdts_model = SDTSModel()
            sdts_model.from_dict(value)
            return sdts_model
        elif name == "noise_gate_model":
            noise_gate_model = NoiseGateModel()
            noise_gate_model.from_dict(value)
            return noise_gate_model
        elif name == "threshold_model":
            threshold_model = ThresholdModel()
            threshold_model.from_dict(value)
            return threshold_model
        elif name == "nn_model":
            nn_model = NNModel()
            nn_model.from_dict(value)
            return nn_model
        elif name == "filtering_model":
            filtering_model = FilteringModel()
            filtering_model.from_dict(value)
            return filtering_model
        return value

    def emit_all_setting_signals(self):
        self.preview_start = self._preview_start
        self.preview_end = self._preview_end
        self.chosen_denoising_method_signal.emit(self.chosen_denoising_method)
        self.chosen_detection_method_signal.emit(self.chosen_detection_method)
