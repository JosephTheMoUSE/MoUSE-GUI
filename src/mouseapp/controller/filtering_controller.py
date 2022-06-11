import logging
from typing import List, Callable

from mouse.classifier import cnn_classifier
from mouse.utils.sound_util import SpectrogramData
from mouseapp.controller.denoising_controller import apply_denoising
from mouseapp.model.main_models import MainModel
from mouseapp.model.utils import Annotation
from mouseapp.controller.utils import process_qt_events, run_background_task, warn_user
from mouseapp.model.settings.utils import Denoising


def _run_NN_filtering(model: MainModel):
    spectrogram = model.spectrogram_model.spectrogram_data
    if spectrogram is None:
        warn_user(model, "There is no audio to run annotation filtering on!")
        return
    chosen_denoising = model.settings_model.chosen_denoising_method
    if chosen_denoising != Denoising.NO_FILTER:
        denoised_spectrogram = apply_denoising(model, spectrogram)
    else:
        denoised_spectrogram = spectrogram

    annotations = model.spectrogram_model.annotation_table_model.annotations

    def _callback(_):
        process_qt_events(model.spectrogram_model.background_task.worker)

    try:
        model.spectrogram_model.progressbar_exists = True
        model.spectrogram_model.progressbar_primary_text = "CNN progress:"
        model.spectrogram_model.progressbar_count = 0
        model.spectrogram_model.progressbar_secondary_text = None

        def _iter_callback(idx, total):
            num_progress = idx + 1
            model.spectrogram_model.progressbar_progress = int(num_progress / total *
                                                               100)
            if num_progress == total:
                model.spectrogram_model.progressbar_progress = None
                model.spectrogram_model.progressbar_secondary_text = "Checking annotations..."
            _callback(None)

        squeak_boxes = [a.to_squeak_box(spectrogram) for a in annotations]
        squeak_boxes = cnn_classifier.classify_USVs(
            denoised_spectrogram,
            squeak_boxes,
            model_name=model.settings_model.filtering_model.model_name,
            batch_size=model.settings_model.filtering_model.batch_size,
            confidence_threshold=model.settings_model.filtering_model.
            confidence_threshold,
            cache_dir=model.settings_model.filtering_model.cache_dir,
            callback=_iter_callback,
            silent=True)

        # Assuming that the model returns squeak boxes in the same order.
        for i, (annotation, squeak_box) in enumerate(zip(annotations, squeak_boxes)):
            if squeak_box.label == 'noise':
                model.spectrogram_model.annotation_table_model.check_annotation(i, True)
                model.spectrogram_model.annotation_table_model.update_selected_field(
                    i, 0)
    finally:
        model.spectrogram_model.progressbar_exists = None
        model.spectrogram_model.progressbar_primary_text = None
        model.spectrogram_model.progressbar_count = None
        model.spectrogram_model.progressbar_secondary_text = None
        model.spectrogram_model.background_task = None


def _run_frequency_filtering(model: MainModel):
    annotations = model.spectrogram_model.annotation_table_model.annotations
    threshold = model.settings_model.filtering_model.frequency_threshold
    for i, annotation in enumerate(annotations):
        if 0.5 * (annotation.freq_start + annotation.freq_end) <= threshold:
            model.spectrogram_model.annotation_table_model.check_annotation(i, True)
            model.spectrogram_model.annotation_table_model.update_selected_field(i, 0)


def filter_annotations(model: MainModel):
    detection_mutex = model.spectrogram_model.main_spectrogram_mutex
    logging.debug("Trying to acquire detection mutex...")
    if detection_mutex.tryLock():
        logging.debug("Detection mutex acquired.")
        model.spectrogram_model.detection_allowed = False
        model.spectrogram_model.classification_allowed = False
        model.spectrogram_model.filtering_allowed = False

        def _filter_annotations():
            try:
                if model.settings_model.filtering_model.frequency_filter:
                    _run_frequency_filtering(model)
                if model.settings_model.filtering_model.neural_network_filter:
                    _run_NN_filtering(model)
            finally:
                model.spectrogram_model.detection_allowed = True
                model.spectrogram_model.classification_allowed = True
                model.spectrogram_model.filtering_allowed = True
                detection_mutex.unlock()

        task = run_background_task(main_model=model,
                                   task=_filter_annotations,
                                   can_be_stopped=True)
        model.spectrogram_model.background_task = task
