import warnings
from typing import List

from mouse.denoising import denoising
from mouse.utils.sound_util import clip_spectrogram, SpectrogramData
from mouseapp.model.main_models import MainModel
from mouseapp.model.settings.utils import Denoising


def set_denoising_for_detection(model: MainModel,
                                spec_list: List[SpectrogramData]):
    chosen_denoising = model.settings_model.chosen_denoising_method

    if chosen_denoising == Denoising.BILATERAL:
        kwargs = model.settings_model.bilateral_model.get_kwargs()
        for spec in spec_list:
            denoising.bilateral_filter(spectrogram=spec,
                                       d=kwargs["d"],
                                       sigma_color=kwargs["sigma_color"],
                                       sigma_space=kwargs["sigma_space"])
    elif chosen_denoising == Denoising.SDTS:
        kwargs = model.settings_model.sdts_model.get_kwargs()
        for spec in spec_list:
            denoising.short_duration_transient_suppression_filter(
                spectrogram=spec,
                alpha=1 - kwargs["noise_decrease"],
                m=kwargs["m"])
    elif chosen_denoising == Denoising.NOISE_GATE:
        kwargs = model.settings_model.noise_gate_model.get_kwargs()
        if kwargs["use_main_spectrogram"]:
            print("Using main spectrogram as noise source")
            noise_spectrogram = clip_spectrogram(
                spec=model.spectrogram_model.spectrogram_data,
                t_start=kwargs["noise_start"],
                t_end=kwargs["noise_end"])
        else:
            print("Using additional spectrogram as noise source")
            if kwargs["noise_spectrogram_data"] is None:
                warnings.warn("Noise spectrogram is not computed")
                # TODO(98): Make the warning show up only once.
                # throw_warning(
                #     model,
                #     ("Before changing other settings, "
                #     "select file with noise or select main spectrogram "
                #     "as noise source")
                return
            noise_spectrogram = clip_spectrogram(
                spec=kwargs["noise_spectrogram_data"],
                t_start=kwargs["noise_start"],
                t_end=kwargs["noise_end"])
        for spec in spec_list:
            denoising.noise_gate_filter(spectrogram=spec,
                                        noise_spectrogram=noise_spectrogram,
                                        n_grad_freq=kwargs["n_grad_freq"],
                                        n_grad_time=kwargs["n_grad_time"],
                                        n_std_thresh=kwargs["n_std_thresh"],
                                        noise_decrease=kwargs["noise_decrease"])
