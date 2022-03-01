from mouse.utils.sound_util import clip_spectrogram
from mouseapp.model.main_models import MainModel


def set_no_filter_preview(model: MainModel):
    spec = model.spectrogram_model.spectrogram_data
    no_filter_model = model.settings_model.no_filter_model
    t_start = model.settings_model.preview_start
    t_end = model.settings_model.preview_end
    model.settings_model.denoising_spectrogram_data = clip_spectrogram(
        spec=spec, t_start=t_start, t_end=t_end)
    no_filter_model.preview_model.preview_data = clip_spectrogram(
        spec=spec, t_start=t_start, t_end=t_end)
