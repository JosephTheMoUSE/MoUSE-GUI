import copy

from mouse.denoising import denoising
from mouse.utils.sound_util import SpectrogramData, clip_spectrogram
from mouseapp.model.main_models import MainModel
from mouseapp.model.settings.utils import Denoising


def apply_bilateral_filter(model: MainModel, spectrogram: SpectrogramData):
    bilateral_model = model.settings_model.bilateral_model
    kwargs = bilateral_model.get_kwargs()

    denoising.bilateral_filter(
        spectrogram=spectrogram,
        d=kwargs["d"],
        sigma_color=kwargs["sigma_color"],
        sigma_space=kwargs["sigma_space"],
    )


def apply_sdts_filter(model: MainModel, spectrogram: SpectrogramData):
    sdts_model = model.settings_model.sdts_model
    kwargs = sdts_model.get_kwargs()

    denoising.short_duration_transient_suppression_filter(spectrogram=spectrogram,
                                                          alpha=1 -
                                                          kwargs["noise_decrease"],
                                                          m=kwargs["m"])


def apply_noise_gate_filter(model: MainModel, spectrogram: SpectrogramData):
    noise_gate_model = model.settings_model.noise_gate_model

    kwargs = noise_gate_model.get_kwargs()
    use_main_spectrogram = kwargs["use_main_spectrogram"]
    # it can happen if the user selects using custom file with noise
    # but haven't loaded any noise file yet
    if not use_main_spectrogram and kwargs["noise_spectrogram_data"] is None:
        raise ValueError()

    if use_main_spectrogram:
        noise_spectrogram = clip_spectrogram(
            spec=model.spectrogram_model.spectrogram_data,
            t_start=kwargs["noise_start"],
            t_end=kwargs["noise_end"],
        )
    else:
        noise_spectrogram = clip_spectrogram(
            spec=kwargs["noise_spectrogram_data"],
            t_start=kwargs["noise_start"],
            t_end=kwargs["noise_end"],
        )

    denoising.noise_gate_filter(
        spectrogram=spectrogram,
        noise_spectrogram=noise_spectrogram,
        n_grad_freq=kwargs["n_grad_freq"],
        n_grad_time=kwargs["n_grad_time"],
        n_std_thresh=kwargs["n_std_thresh"],
        noise_decrease=kwargs["noise_decrease"],
    )


def apply_denoising(model: MainModel, spectrogram):
    denoising_method: Denoising = model.settings_model.chosen_denoising_method
    denoised_spectrogram = copy.deepcopy(spectrogram)

    if denoising_method == Denoising.BILATERAL:
        apply_bilateral_filter(model, denoised_spectrogram)
    elif denoising_method == Denoising.NOISE_GATE:
        apply_noise_gate_filter(model, denoised_spectrogram)
    elif denoising_method == Denoising.SDTS:
        apply_sdts_filter(model, denoised_spectrogram)
    else:
        raise NotImplementedError(
            f"Denoising method `{denoising_method}` is not supported!")
    return denoised_spectrogram
