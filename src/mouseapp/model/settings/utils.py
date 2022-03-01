import time
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
        self._time_between_updates = 1.
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
