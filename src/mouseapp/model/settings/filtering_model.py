from PySide6.QtCore import Signal

from mouseapp.model.utils import SerializableModel


class FilteringModel(SerializableModel):

    frequency_filter_changed = Signal(bool)
    frequency_threshold_changed = Signal(float)

    def __init__(self):
        super().__init__()

        self._default_values = {
            "_frequency_filter": False,
            "_frequency_threshold": 18000.,
        }
        self._frequency_filter: bool = False
        self._frequency_threshold: float = 0.
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

    def emit_all_setting_signals(self):
        self.frequency_filter_changed.emit(self.frequency_filter)
        self.frequency_threshold_changed.emit(self.frequency_threshold)

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
