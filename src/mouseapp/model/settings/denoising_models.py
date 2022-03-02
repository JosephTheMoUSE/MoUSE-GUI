from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal
from mouse.utils.sound_util import SpectrogramData
from mouseapp.model.settings.utils import PreviewModel
from mouseapp.model.utils import SerializableModel


class NoFilterModel(QObject):

    def __init__(self):
        super().__init__()
        self._preview_model: PreviewModel = PreviewModel()

    @property
    def preview_model(self):
        return self._preview_model

    def emit_all_setting_signals(self):
        self.preview_model.emit_time_setting_signals()


class BilateralModel(SerializableModel):
    # signals
    d_changed = Signal(int)
    sigma_color_changed = Signal(float)
    sigma_space_changed = Signal(float)

    def __init__(self):
        super().__init__()
        self._dict_denylist.add("preview_model")
        self._preview_model: PreviewModel = PreviewModel()

        self._default_values = {
            "_d": 5,
            "_sigma_color": 150.0,
            "_sigma_space": 150.0,
        }
        self._d: int = 0
        self._sigma_color: float = 0
        self._sigma_space: float = 0
        self.set_default_values()

    def __repr__(self):
        return (f"Bilateral:d={self.d},"
                f"sigma_color={self.sigma_color},"
                f"sigma_space={self.sigma_space};")

    def set_default_values(self):
        for key, val in self._default_values.items():
            setattr(self, key, val)

    @property
    def d(self):
        return self._d

    @d.setter
    def d(self, value: int):
        self._d = value
        self.d_changed.emit(value)

    @property
    def sigma_color(self):
        return self._sigma_color

    @sigma_color.setter
    def sigma_color(self, value: float):
        self._sigma_color = value
        self.sigma_color_changed.emit(value)

    @property
    def sigma_space(self):
        return self._sigma_space

    @sigma_space.setter
    def sigma_space(self, value: float):
        self._sigma_space = value
        self.sigma_space_changed.emit(value)

    @property
    def preview_model(self):
        return self._preview_model

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

    def emit_all_setting_signals(self):
        self.d = self._d
        self.sigma_color = self._sigma_color
        self.sigma_space = self._sigma_space


class SDTSModel(SerializableModel):
    # signals
    noise_decrease_changed = Signal(float)
    m_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self._dict_denylist.add("preview_model")
        self._preview_model: PreviewModel = PreviewModel()

        self._default_values = {
            "_noise_decrease": 0.5,
            "_m": 3,
        }
        self._noise_decrease: float = 0
        self._m: int = 0
        self.set_default_values()

    def __repr__(self):
        return f"SDTS:noise_decrease={self.noise_decrease},m={self.m};"

    def set_default_values(self):
        for key, val in self._default_values.items():
            setattr(self, key, val)

    @property
    def m(self):
        return self._m

    @m.setter
    def m(self, value: int):
        self._m = value
        self.m_changed.emit(value)

    @property
    def noise_decrease(self):
        return self._noise_decrease

    @noise_decrease.setter
    def noise_decrease(self, value: float):
        self._noise_decrease = value
        self.noise_decrease_changed.emit(value)

    @property
    def preview_model(self):
        return self._preview_model

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

    def emit_all_setting_signals(self):
        self.m = self._m
        self.noise_decrease = self._noise_decrease


class NoiseGateModel(SerializableModel):
    # signals
    n_grad_freq_changed = Signal(int)
    n_grad_time_changed = Signal(int)
    n_std_thresh_changed = Signal(float)
    noise_decrease_changed = Signal(float)
    noise_start_changed = Signal(float)
    noise_end_changed = Signal(float)
    noise_spectrogram_data_changed = Signal()
    use_main_spectrogram_changed = Signal(tuple)
    noise_audio_changed = Signal(Path)
    passive_noise_audio_changed = Signal(Path)

    def __init__(self):
        super().__init__()
        self._dict_denylist.update(["preview_model", "noise_spectrogram_data"])
        self._preview_model: PreviewModel = PreviewModel()

        self._default_values = {
            "_n_grad_freq": 3,
            "_n_grad_time": 3,
            "_n_std_thresh": 1.0,
            "_noise_decrease": 0.5,
            "_noise_start": 0.0,
            "_noise_end": 1.0,
            "_noise_spectrogram_data": None,
            "_noise_audio_file": None,
            "_use_main_spectrogram": True,
        }
        self._n_grad_freq: int = 0
        self._n_grad_time: int = 0
        self._n_std_thresh: float = 0
        self._noise_decrease: float = 0
        self._noise_start: float = 0
        self._noise_end: float = 0
        self._use_main_spectrogram: bool = True
        self._noise_audio_file: Optional[Path] = None
        self._noise_spectrogram_data: Optional[SpectrogramData] = None
        self.set_default_values()

    def __repr__(self):
        noise_audio = ("same" if self.noise_audio_file is None and
                       self.use_main_spectrogram else self.noise_audio_file)

        return (f"Noise-gate:gradient_pixels_number_frequency={self.n_grad_freq},"
                f"gradient_pixels_number_time={self.n_grad_time},"
                f"number_std_cutoff={self.n_std_thresh},"
                f"noise_decrease={self.noise_decrease},"
                f"noise_audio_file={noise_audio},"
                f"noise_start={self.noise_start},"
                f"noise_end={self.noise_end};")

    def set_default_values(self):
        for key, val in self._default_values.items():
            setattr(self, key, val)

    @property
    def n_grad_freq(self):
        return self._n_grad_freq

    @n_grad_freq.setter
    def n_grad_freq(self, value: int):
        self._n_grad_freq = value
        self.n_grad_freq_changed.emit(value)

    @property
    def n_grad_time(self):
        return self._n_grad_time

    @n_grad_time.setter
    def n_grad_time(self, value: int):
        self._n_grad_time = value
        self.n_grad_time_changed.emit(value)

    @property
    def n_std_thresh(self):
        return self._n_std_thresh

    @n_std_thresh.setter
    def n_std_thresh(self, value: float):
        self._n_std_thresh = value
        self.n_std_thresh_changed.emit(value)

    @property
    def noise_decrease(self):
        return self._noise_decrease

    @noise_decrease.setter
    def noise_decrease(self, value: float):
        self._noise_decrease = value
        self.noise_decrease_changed.emit(value)

    @property
    def noise_start(self):
        return self._noise_start

    @noise_start.setter
    def noise_start(self, value: float):
        self._noise_start = value
        self.noise_start_changed.emit(value)

    @property
    def noise_end(self):
        return self._noise_end

    @noise_end.setter
    def noise_end(self, value: float):
        self._noise_end = value
        self.noise_end_changed.emit(value)

    @property
    def noise_audio_file(self):
        return self._noise_audio_file

    @noise_audio_file.setter
    def noise_audio_file(self, value: Path):
        self._noise_audio_file = value
        if not self.use_main_spectrogram and self.noise_audio_file is not None:
            "emmiting signal"
            self.noise_audio_changed.emit(self.noise_audio_file)

    def set_noise_audio_file_passive_signal(self, value: Path):
        self._noise_audio_file = value
        self.passive_noise_audio_changed.emit(self.noise_audio_file)

    @property
    def noise_spectrogram_data(self):
        return self._noise_spectrogram_data

    @noise_spectrogram_data.setter
    def noise_spectrogram_data(self, value: SpectrogramData):
        self._noise_spectrogram_data = value
        self.noise_spectrogram_data_changed.emit()

    @property
    def use_main_spectrogram(self):
        return self._use_main_spectrogram

    @use_main_spectrogram.setter
    def use_main_spectrogram(self, value: bool):
        self._use_main_spectrogram = value
        self.use_main_spectrogram_changed.emit((value, self.noise_audio_file))

    @property
    def preview_model(self):
        return self._preview_model

    def get_kwargs(self):
        kwargs = dict()
        for key in self._default_values.keys():
            value = getattr(self, key)
            kwargs[key[1:]] = value

        return kwargs

    def _value_to_dict(self, name, value):
        # if the user decided they want to use main spectrogram as noice
        # ther is no need to store the extra file

        if name == "use_main_spectrogram" and self.noise_audio_file is None:
            return True
        if name != "noise_audio_file":
            return value
        if self.use_main_spectrogram or value is None:
            return None
        return str(value)

    def _value_from_dict(self, name, value):
        if name == "noise_audio_file" and value is not None:
            return Path(value)
        return value

    def emit_all_setting_signals(self):
        self.noise_audio_file = self._noise_audio_file
        self.n_grad_freq = self._n_grad_freq
        self.n_grad_time = self._n_grad_time
        self.n_std_thresh = self._n_std_thresh
        self.noise_decrease = self._noise_decrease
        self.noise_start = self._noise_start
        self.noise_end = self._noise_end
        self.use_main_spectrogram = self._use_main_spectrogram
