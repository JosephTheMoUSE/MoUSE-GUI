import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PySide6.QtCore import QObject, Signal, QMutex
from mouse.utils.sound_util import SpectrogramData


class PreviewModel(QObject):
    preview_changed = Signal(SpectrogramData)

    def __init__(self):
        super().__init__()
        self._preview_data: Optional[SpectrogramData] = None
        self._last_update: float = time.time()
        # minimum time[s] between preview updates
        self._time_between_updates = 1.0
        # mutexes
        self._initial_mutex = QMutex()
        self._calculation_mutex = QMutex()

    @property
    def initial_mutex(self):
        return self._initial_mutex

    @property
    def calculation_mutex(self):
        return self._calculation_mutex

    @property
    def preview_data(self):
        return self._preview_data

    @preview_data.setter
    def preview_data(self, value: Optional[SpectrogramData]):
        self.preview_changed.emit(value)
        self._preview_data = value

    @property
    def time_between_updates(self):
        return self._time_between_updates


class Denoising(str, Enum):
    NO_FILTER = "no filter"
    BILATERAL = "bilateral filter"
    SDTS = "short duration transient suppression filter"
    NOISE_GATE = "noise gate filter"


class Detection(str, Enum):
    GAC = "GAC detection"
    NN = "Neural network detection"


@dataclass(frozen=True)
class OptimisationResult:
    metric_name: str
    metric: float
    precision: Optional[float]
    recall: Optional[float]
    box_count: int
    sigma: float
    iters: int
    balloon: int
    threshold: float
    flood_threshold: float
    smoothing: int

    def __gt__(self, other):
        return self.metric > other.metric

    def __lt__(self, other):
        return self.metric < other.metric

    def __str__(self):
        optional_metrics = ""
        if None not in {self.precision, self.recall}:
            optional_metrics = (
                f"(precision: {self.precision:.3f}, recall: {self.recall:.3f})")
        return (
            f"Trial score ({self.metric_name}): {self.metric:.3f} {optional_metrics}\n"
            f"Score was calculated based on {self.box_count} detections.\n"
            f"Trial configuration:\n\tsigma = {self.sigma}\n\titers = {self.iters}\n\tballoon = {self.balloon}\n\tthresold = {self.threshold}\n\tflood_threshold = {self.flood_threshold}\n\tsmoothing = {self.smoothing}"
        )
