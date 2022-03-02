from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

import numpy as np
from PySide6.QtCore import QThread, QObject, Signal
from mouse.utils.data_util import SqueakBox
from mouse.utils.sound_util import SpectrogramData
from mouseapp.model import constants


@dataclass
class MouseProject:
    name: str
    path: Path

    def __hash__(self):  # noqa D105
        return self.path.__hash__()

    def __str__(self):  # noqa D105
        return f"({repr(self.name)}, {repr(str(self.path))})"

    def __eq__(self, other):  # noqa D105
        if not isinstance(other, MouseProject):
            return False
        return other.path == self.path

    @staticmethod
    def from_string(value):
        name, path = eval(value)
        return MouseProject(name=name, path=Path(path))


@dataclass(frozen=True)
class BackgroundTask:
    """Container class for storing references to a background task.

    This class contains 3 elements:
    `thread` - the thread under which the task is executed
    `worker` - a QObject executing the task
    `kill_signal` - a Signal sending of which will finish the `thread`. The
                    `thread` won't stop immediately, it will be finalized
                    only when the signal is processed. This value should be
                    set to `None` if `worker` prevents events from
                    `QEventLoop` to be processed.
    """

    thread: QThread
    worker: QObject
    kill_signal: Optional[Signal]

    def is_killable(self):
        return self.kill_signal is not None

    def kill(self):
        try:
            logging.info("Stopping background task...")
            self.kill_signal.emit()
        except RuntimeError:  # Internal C++ object (Worker) already deleted.
            pass
            print("Internal C++ object (Worker) already deleted.")


class Annotation:

    def __init__(self,
                 time_start,
                 time_end,
                 freq_start,
                 freq_end,
                 label=None,
                 table_data=None):
        self._time_start = time_start
        self._time_end = time_end
        self._freq_start = freq_start
        self._freq_end = freq_end
        self._label = label
        self._checked = False
        if table_data is None:
            self.table_data = defaultdict(lambda: "")
        else:
            self.table_data = table_data
        self.table_data[constants.COL_BEGIN_TIME] = time_start
        self.table_data[constants.COL_END_TIME] = time_end
        self.table_data[constants.COL_LOW_FREQ] = freq_start
        self.table_data[constants.COL_HIGH_FREQ] = freq_end
        self.table_data[constants.COL_USV_LABEL] = label

    @property
    def time_start(self):
        return self._time_start

    @time_start.setter
    def time_start(self, value):
        self._time_start = value
        self.table_data[constants.COL_BEGIN_TIME] = value

    @property
    def time_end(self):
        return self._time_end

    @time_end.setter
    def time_end(self, value):
        self._time_end = value
        self.table_data[constants.COL_END_TIME] = value

    @property
    def freq_start(self):
        return self._freq_start

    @freq_start.setter
    def freq_start(self, value):
        self._freq_start = value
        self.table_data[constants.COL_LOW_FREQ] = value

    @property
    def freq_end(self):
        return self._freq_end

    @freq_end.setter
    def freq_end(self, value):
        self._freq_end = value
        self.table_data[constants.COL_HIGH_FREQ] = value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value
        self.table_data[constants.COL_USV_LABEL] = value

    @property
    def checked(self):
        return self._checked

    @checked.setter
    def checked(self, value):
        self._checked = value

    def to_dict(self):
        return {
            "time_start": self.time_start,
            "time_end": self.time_end,
            "freq_start": self.freq_start,
            "freq_end": self.freq_end,
            "label": self.label,
            "table_data": dict(self.table_data),
        }

    def to_squeak_box(self, spec_data: SpectrogramData):
        # cast to pixels
        t_start = np.abs(spec_data.times - self.time_start).argmin()
        t_end = np.abs(spec_data.times - self.time_end).argmin()
        freq_start = np.abs(spec_data.freqs - self.freq_start).argmin()
        freq_end = np.abs(spec_data.freqs - self.freq_end).argmin()
        return SqueakBox(
            freq_start=int(freq_start),
            freq_end=int(freq_end),
            t_start=int(t_start),
            t_end=int(t_end),
            label=self.label,
        )

    @staticmethod
    def from_dict(**values) -> Annotation:
        annotation = Annotation(**values)
        annotation.table_data = defaultdict(lambda: "", annotation.table_data)
        return annotation

    @staticmethod
    def from_squeak_box(squeak_box: SqueakBox,
                        spec_data: SpectrogramData,
                        table_data: Dict = None) -> Annotation:
        t_start, t_end = spec_data.times[[squeak_box.t_start, squeak_box.t_end]]
        freq_start, freq_end = spec_data.freqs[
            [squeak_box.freq_start, squeak_box.freq_end]
        ]
        annotation = Annotation(
            time_start=float(t_start),
            time_end=float(t_end),
            freq_start=float(freq_start),
            freq_end=float(freq_end),
            label=squeak_box.label if squeak_box.label else "Unknown",
        )

        for key, val in table_data.items():
            annotation.table_data[key] = val
        return annotation


class SerializableModel(QObject):

    def __init__(self):
        super(SerializableModel, self).__init__()
        self._dict_denylist = set(dir(QObject))
        self._dict_denylist.add("_dict_denylist")

    def to_dict(self):
        result = {}
        for property_name, value in self:
            result[property_name] = self._value_to_dict(property_name, value)
        return result

    def from_dict(self, property_dict):
        for attribute_name, value in property_dict.items():
            assert attribute_name in dir(type(self))
            assert self._is_settable_attribute(attribute_name)
            evaluated_value = self._value_from_dict(attribute_name, value)
            setattr(self, attribute_name, evaluated_value)

    def _is_settable_attribute(self, name):
        return not (name.startswith("__") or callable(getattr(self, name)) or
                    name in self._dict_denylist or name.endswith("attr_name"))

    def __iter__(self):
        """Iterate through attributes and their values.

        Omits callable and magic attributes.
        """
        for attribute_name in dir(type(self)):
            if not self._is_settable_attribute(attribute_name):
                continue
            yield attribute_name, getattr(self, attribute_name)

    def _value_to_dict(self, name, value):
        """Map attribute value when `to_dict` method is called."""
        raise NotImplementedError("")

    def _value_from_dict(self, name, value):
        """Map attribute value when from_dict` method is called."""
        raise NotImplementedError("")
