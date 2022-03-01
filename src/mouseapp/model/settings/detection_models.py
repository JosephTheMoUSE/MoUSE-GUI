from functools import partial
from pathlib import Path
from typing import List, Optional

import appdirs
import numpy as np
from PySide6.QtCore import Signal
from mouse.nn_detection.neural_network import PRETRAINED_MODELS_CHECKPOINTS
from mouse.utils.data_util import SqueakBox
from mouse.utils.sound_util import SpectrogramData
from mouseapp.model.settings.utils import PreviewModel
from mouseapp.model.utils import BackgroundTask, SerializableModel
from skimage import morphology, segmentation


class DetectionPreviewModel(PreviewModel):
    detections_changed = Signal(tuple)
    method_allowed_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self._detections: List[SqueakBox] = []
        self._is_method_allowed: bool = True
        self._calculation_task: Optional[BackgroundTask] = None

    @property
    def is_method_allowed(self):
        return self._is_method_allowed

    @is_method_allowed.setter
    def is_method_allowed(self, value):
        self._is_method_allowed = value
        self.method_allowed_changed.emit(value)

    @property
    def detections(self):
        return self._detections

    @detections.setter
    def detections(self, value: List[SqueakBox]):
        spec_height = self._preview_data.get_height()
        self.detections_changed.emit((value, spec_height))
        self._detections = value

    @property
    def calculation_task(self) -> Optional[BackgroundTask]:
        return self._calculation_task

    @calculation_task.setter
    def calculation_task(self, value: BackgroundTask):
        self._calculation_task = value


class GACPreviewModel(DetectionPreviewModel):
    preview_changed = Signal(tuple)

    def __init__(self):
        super().__init__()
        self._last_gac_step: float = 0.
        self._initial_level_set: Optional[np.ndarray] = None
        # minimum time[s] between redrawing gac updates
        self._time_between_gac_steps = .5

    @property
    def initial_level_set(self):
        return self._initial_level_set

    @initial_level_set.setter
    def initial_level_set(self, value: Optional[np.ndarray]):
        self._initial_level_set = value

    @property
    def last_gac_step(self):
        return self._last_gac_step

    @last_gac_step.setter
    def last_gac_step(self, value: float):
        self._last_gac_step = value

    @property
    def time_between_gac_steps(self):
        return self._time_between_gac_steps

    @property
    def is_gac_allowed(self):
        return self._is_method_allowed

    @is_gac_allowed.setter
    def is_gac_allowed(self, value: bool):
        self._is_method_allowed = value
        self.method_allowed_changed.emit(value)

    @property
    def preview_data(self):
        return self._preview_data

    @preview_data.setter
    def preview_data(self, value: Optional[SpectrogramData]):
        self.preview_changed.emit((value, self._initial_level_set))
        self._preview_data = value


class DetectionModel(SerializableModel):

    def __init__(self):
        super(DetectionModel, self).__init__()
        self._default_values = {}

    def set_default_values(self):
        for key, val in self._default_values.items():
            setattr(self, key, val)

    def get_kwargs(self):
        return {(key if key[0] != '_' else key[1:]): getattr(self, key)
                for key in self._default_values.keys()}

    def _value_to_dict(self, name, value):
        return value

    def _value_from_dict(self, name, value):
        return value


class GACModel(DetectionModel):
    # signals
    iterations_changed = Signal(int)
    smoothing_changed = Signal(int)
    threshold_changed = Signal(float)
    flood_threshold_changed = Signal(float)
    balloon_changed = Signal(float)
    alpha_changed = Signal(float)
    sigma_changed = Signal(float)

    def __init__(self):
        super().__init__()
        self._dict_denylist.add("preview_model")
        self._preview_model: GACPreviewModel = GACPreviewModel()

        self._default_values = {
            "_iterations": 15,
            "_smoothing": 3,
            "_threshold": 0.8,
            "_balloon": -1,
            "_alpha": 200,
            "_sigma": 7,
            "_flood_threshold": 0.75,
        }
        self._iterations: int = 0
        self._smoothing: int = 0
        self._threshold: float = 0.
        self._balloon: float = 0.
        self._alpha: float = 0.
        self._sigma: int = 0
        self._flood_threshold: float = 0.95
        self.set_default_values()

    def __repr__(self):
        return (f'GAC:iterations={self.iterations},'
                f'smoothing={self.smoothing},'
                f'threshold={self.threshold},'
                f'balloon={self.smoothing},'
                f'alpha={self.alpha},'
                f'sigma={self.sigma},'
                f'flood_threshold={self.flood_threshold};')

    @property
    def iterations(self):
        return self._iterations

    @iterations.setter
    def iterations(self, value: int):
        self._iterations = value
        self.iterations_changed.emit(value)

    @property
    def threshold(self):
        return self._threshold

    @threshold.setter
    def threshold(self, value: float):
        self._threshold = value
        self.threshold_changed.emit(value)

    @property
    def balloon(self):
        return self._balloon

    @balloon.setter
    def balloon(self, value: bool):
        self._balloon = value
        self.balloon_changed.emit(value)

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, value: float):
        self._alpha = value
        self.alpha_changed.emit(value)

    @property
    def sigma(self):
        return self._sigma

    @sigma.setter
    def sigma(self, value: float):
        self._sigma = value
        self.sigma_changed.emit(value)

    @property
    def smoothing(self):
        return self._smoothing

    @smoothing.setter
    def smoothing(self, value: int):
        self._smoothing = value
        self.smoothing_changed.emit(value)

    @property
    def flood_threshold(self):
        return self._flood_threshold

    @flood_threshold.setter
    def flood_threshold(self, value):
        self._flood_threshold = value
        self.flood_threshold_changed.emit(value)

    @property
    def preview_model(self) -> GACPreviewModel:
        return self._preview_model

    def get_kwargs(self):

        def level_set_fn(spec: np.ndarray):
            mask = spec <= self._flood_threshold
            seed = np.ones_like(mask)
            mask[:, 0] = 0
            mask[:, -1] = 0
            mask[0, :] = 0
            mask[-1, :] = 0
            seed[:, 0] = 0
            seed[:, -1] = 0
            seed[0, :] = 0
            seed[-1, :] = 0
            return morphology.reconstruction(seed, mask, method='erosion')

        kwargs = {
            "preprocessing_fn":
                partial(segmentation.inverse_gaussian_gradient,
                        sigma=self._sigma,
                        alpha=self._alpha),
            "level_set_fn":
                level_set_fn
        }

        for key in self._default_values.keys():
            value = getattr(self, key)
            if key in {"_alpha", "_sigma", "_flood_threshold"}:
                # these are arguments for level set and preprocessing functions
                continue
            else:
                kwargs[key[1:]] = value

        return kwargs

    def emit_all_setting_signals(self):
        self.iterations = self._iterations
        self.smoothing = self._smoothing
        self.threshold = self._threshold
        self.balloon = self._balloon
        self.alpha = self._alpha
        self.sigma = self._sigma
        self.flood_threshold = self._flood_threshold


class NNModel(DetectionModel):
    model_name_changed = Signal(str)
    model_batch_size_changed = Signal(int)
    model_confidence_threshold_changed = Signal(float)

    def __init__(self):
        super(NNModel, self).__init__()
        self._dict_denylist.add("preview_model")
        self._preview_model: DetectionPreviewModel = DetectionPreviewModel()

        self._default_values = {
            '_model_name':
                'f-rcnn-custom',
            '_batch_size':
                1,
            '_confidence_threshold':
                0.2,
            '_cache_dir':
                Path(appdirs.user_data_dir(appname='MoUSE')) /
                'nn_pretrained_models_cache'
        }
        self._model_name = 'F-RCNN-custom'
        self._batch_size = 1
        self._confidence_threshold = 0.2
        self._cache_dir = None
        self.set_default_values()

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value: str):
        if value not in PRETRAINED_MODELS_CHECKPOINTS:
            raise ValueError(f'Model type should be one of '
                             f'{list(PRETRAINED_MODELS_CHECKPOINTS.keys())} '
                             f'but found {value}')
        self._model_name = value
        self.model_name_changed.emit(value)

    @property
    def batch_size(self):
        return int(self._batch_size)

    @batch_size.setter
    def batch_size(self, value: int):
        if value <= 0:
            raise ValueError('Batch size should be greater than zero')
        self._batch_size = int(value)
        self.model_batch_size_changed.emit(value)

    @property
    def confidence_threshold(self):
        return self._confidence_threshold

    @confidence_threshold.setter
    def confidence_threshold(self, value: float):
        if value < 0:
            raise ValueError('Confidence threshold should be in range [0, 1]')
        self._confidence_threshold = value
        self.model_confidence_threshold_changed.emit(value)

    @property
    def preview_model(self):
        return self._preview_model

    def emit_all_setting_signals(self):
        self.model_name = self._model_name
        self.batch_size = self._batch_size
        self.confidence_threshold = self._confidence_threshold

    def __repr__(self):
        return (f'NN:model_name={self.model_name},'
                f'confidence_threshold={self.confidence_threshold},'
                f'batch_size={self.batch_size},')
