import time
from pathlib import Path

import torchaudio
from mouse.utils.sound_util import clip_spectrogram, spectrogram
from mouseapp.controller import denoising_controller
from mouseapp.controller.utils import warn_user, run_background_task, float_convert
from mouseapp.model.main_models import MainModel


def set_n_grad_freq(model: MainModel, value: int):
    if check_change_preconditions(model):
        model.settings_model.noise_gate_model.n_grad_freq = value
    else:
        model.settings_model.noise_gate_model.n_grad_freq = (
            model.settings_model.noise_gate_model.n_grad_freq)


def set_n_grad_time(model: MainModel, value: int):
    if check_change_preconditions(model):
        model.settings_model.noise_gate_model.n_grad_time = value
    else:
        model.settings_model.noise_gate_model.n_grad_time = (
            model.settings_model.noise_gate_model.n_grad_time)


def set_n_std_thresh(model: MainModel, value: str):
    if check_change_preconditions(model):
        f_value = float_convert(value)
        model.settings_model.noise_gate_model.n_std_thresh = f_value
    else:
        model.settings_model.noise_gate_model.n_std_thresh = (
            model.settings_model.noise_gate_model.n_std_thresh)


def set_noise_decrease(model: MainModel, value: float):
    if check_change_preconditions(model):
        model.settings_model.noise_gate_model.noise_decrease = value
    else:
        model.settings_model.noise_gate_model.noise_decrease = (
            model.settings_model.noise_gate_model.noise_decrease)


def set_noise_start_end(model: MainModel, noise_start: str, noise_end: str):
    if check_change_preconditions(model):
        f_noise_start = float_convert(noise_start)
        f_noise_end = float_convert(noise_end)
        if f_noise_start < f_noise_end:
            model.settings_model.noise_gate_model.noise_start = f_noise_start
            model.settings_model.noise_gate_model.noise_end = f_noise_end
    else:
        model.settings_model.noise_gate_model.noise_start = (
            model.settings_model.noise_gate_model.noise_start)
        model.settings_model.noise_gate_model.noise_end = (
            model.settings_model.noise_gate_model.noise_end)


def set_use_main_spectrogram(model: MainModel, value: bool):
    model.settings_model.noise_gate_model.use_main_spectrogram = value


def load_noise_audio(model: MainModel, file: Path):
    if model.spectrogram_model.spectrogram_calculator is None:
        warn_user(model, "Before loading audio with noise, load main recordings")
        return
    # there is no point recalculating the spectrogram if we already have it
    if (model.settings_model.noise_gate_model.noise_audio_file == file and
            model.settings_model.noise_gate_model.noise_spectrogram_data is not None):
        return

    spectrogram_model = model.spectrogram_model
    waveform, sample_rate = torchaudio.load(file)
    model.settings_model.noise_gate_model.noise_spectrogram_data = spectrogram(
        waveform.squeeze(),
        sample_rate=sample_rate,
        spec_calculator=spectrogram_model.spectrogram_calculator,
        n_fft=spectrogram_model.n_fft,
        win_length=spectrogram_model.win_length,
        hop_length=spectrogram_model.hop_length,
        power=spectrogram_model.power,
    )
    model.settings_model.noise_gate_model.set_noise_audio_file_passive_signal(file)


def restore_default_noise_gate_values(model: MainModel):
    model.settings_model.noise_gate_model.set_default_values()
    model.settings_model.noise_gate_model.emit_all_setting_signals()


def emit_settings_signals(model: MainModel):
    model.settings_model.noise_gate_model.emit_all_setting_signals()


def check_change_preconditions(model: MainModel):
    if (model.settings_model.noise_gate_model.noise_audio_file is None and
            not model.settings_model.noise_gate_model.use_main_spectrogram):
        # TODO(98): Make the warning show up only once.
        # throw_warning(
        #     model,
        #     ("Before changing other settings, "
        #     "select file with noise or select main spectrogram "
        #     "as noise source"))
        return False
    return True


def set_noise_gate_preview(model: MainModel):
    noise_gate_model = model.settings_model.noise_gate_model
    kwargs = noise_gate_model.get_kwargs()
    use_main_spectrogram = kwargs["use_main_spectrogram"]
    # it can happen if the user selects using custom file with noise
    # but haven't loaded any noise file yet
    if not use_main_spectrogram and kwargs["noise_spectrogram_data"] is None:
        return
    inital_mutex = noise_gate_model.preview_model.initial_mutex
    calculation_mutex = noise_gate_model.preview_model.calculation_mutex

    def set_preview():
        # prevent too frequent updates
        time.sleep(noise_gate_model.preview_model.time_between_updates)

        calculation_mutex.lock()
        inital_mutex.unlock()
        spec = model.spectrogram_model.spectrogram_data
        t_start = model.settings_model.preview_start
        t_end = model.settings_model.preview_end
        orginal_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)
        model.settings_model.denoising_spectrogram_data = orginal_spec

        preview_spec = clip_spectrogram(spec=spec, t_start=t_start, t_end=t_end)

        denoising_controller.apply_noise_gate_filter(model=model,
                                                     spectrogram=preview_spec)

        noise_gate_model.preview_model.preview_data = preview_spec
        calculation_mutex.unlock()

    if inital_mutex.tryLock():
        run_background_task(main_model=model, task=set_preview, can_be_stopped=False)
