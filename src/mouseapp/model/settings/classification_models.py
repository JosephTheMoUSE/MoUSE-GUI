from PySide6.QtCore import Signal

from mouseapp.model.utils import SerializableModel


class ThresholdModel(SerializableModel):
    # signals
    threshold_changed = Signal(float)
    low_label_changed = Signal(str)
    high_label_changed = Signal(str)

    def __init__(self):
        super().__init__()

        self._default_values = {
            "_threshold": 30000.0,
            "_label_low": "low freq",
            "_label_high": "high freq",
        }
        self._threshold: float = 0
        self._label_low: str = ""
        self._label_high: str = ""
        self.set_default_values()

    def set_default_values(self):
        for key, val in self._default_values.items():
            setattr(self, key, val)

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, value: float):
        self._threshold = value
        self.threshold_changed.emit(value)

    @property
    def label_low(self) -> str:
        return self._label_low

    @label_low.setter
    def label_low(self, value: str):
        self._label_low = value
        self.low_label_changed.emit(value)

    @property
    def label_high(self) -> str:
        return self._label_high

    @label_high.setter
    def label_high(self, value: str):
        self._label_high = value
        self.high_label_changed.emit(value)

    def _value_to_dict(self, name, value):
        return value

    def _value_from_dict(self, name, value):
        return value

    def emit_all_setting_signals(self):
        self.threshold = self._threshold
        self.label_high = self._label_high
        self.label_low = self._label_low
