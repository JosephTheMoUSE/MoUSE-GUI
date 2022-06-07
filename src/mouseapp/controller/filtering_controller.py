from typing import List

from mouse.classifier import cnn_classifier
from mouse.utils.sound_util import SpectrogramData
from mouseapp.controller.denoising_controller import apply_denoising
from mouseapp.model.main_models import MainModel
from mouseapp.model.utils import Annotation
from mouseapp.model.settings.utils import Denoising


def _run_NN_filtering(model: MainModel,
                      spectrogram: SpectrogramData,
                      annotations: List[Annotation]):

    def _callback(idx, total):
        return

    squeak_boxes = [a.to_squeak_box(spectrogram) for a in annotations]
    squeak_boxes = cnn_classifier.classify_USVs(
        spectrogram,
        squeak_boxes,
        model_name=model.settings_model.filtering_model.model_name,
        batch_size=model.settings_model.filtering_model.batch_size,
        confidence_threshold=model.settings_model.filtering_model.confidence_threshold,
        cache_dir=model.settings_model.filtering_model.cache_dir,
        callback=_callback,
        silent=True)

    # Assuming that the model returns squeak boxes in the same order.
    for i, (annotation, squeak_box) in enumerate(zip(annotations, squeak_boxes)):
        if squeak_box.label == 'noise':
            model.spectrogram_model.annotation_table_model.check_annotation(i, True)
            model.spectrogram_model.annotation_table_model.update_selected_field(i, 0)


def filter_annotations(model: MainModel):
    annotations = model.spectrogram_model.annotation_table_model.annotations
    if model.settings_model.filtering_model.frequency_filter:
        threshold = model.settings_model.filtering_model.frequency_threshold
        for i, annotation in enumerate(annotations):
            if 0.5 * (annotation.freq_start + annotation.freq_end) <= threshold:
                model.spectrogram_model.annotation_table_model.check_annotation(i, True)
                model.spectrogram_model.annotation_table_model.update_selected_field(
                    i, 0)
    if model.settings_model.filtering_model.neural_network_filter:
        spectrogram = model.spectrogram_model.spectrogram_data
        chosen_denoising = model.settings_model.chosen_denoising_method
        if chosen_denoising != Denoising.NO_FILTER:
            denoised_spectrogram = apply_denoising(model, spectrogram)
        else:
            denoised_spectrogram = spectrogram
        _run_NN_filtering(model,
                          spectrogram=denoised_spectrogram,
                          annotations=annotations)
