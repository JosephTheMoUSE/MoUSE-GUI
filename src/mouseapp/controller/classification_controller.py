import copy
import logging
from typing import Callable

from mouse.rule_based_classifier.simple_classifier import classify_USVs

from mouseapp.controller.utils import run_background_task, process_qt_events
from mouseapp.model.main_models import MainModel


def run_selected_classification(model: MainModel):
    detection_mutex = model.spectrogram_model.detection_mutex
    logging.debug("Trying to acquire detection mutex...")
    if detection_mutex.tryLock():
        logging.debug("Detection mutex acquired.")
        model.spectrogram_model.detection_allowed = False

        annotation_count = len(
            model.spectrogram_model.annotation_table_model.annotations)

        def callback():
            process_qt_events(model.spectrogram_model.background_task.worker)
            num_progress = model.spectrogram_model.progressbar_count
            model.spectrogram_model.progressbar_progress = int(num_progress /
                                                               annotation_count * 100)
            model.spectrogram_model.progressbar_count += 1

        def classify_USVs():
            try:
                model.spectrogram_model.progressbar_exists = True
                model.spectrogram_model.progressbar_primary_text = (
                    "Classification progress:")
                model.spectrogram_model.progressbar_count = 0
                model.spectrogram_model.progressbar_secondary_text = None

                make_frequency_classification(model, callback)
            finally:
                model.spectrogram_model.detection_allowed = True
                model.spectrogram_model.progressbar_exists = False
                model.spectrogram_model.progressbar_primary_text = None
                model.spectrogram_model.progressbar_count = None
                model.spectrogram_model.progressbar_secondary_text = None
                detection_mutex.unlock()

        task = run_background_task(main_model=model,
                                   task=classify_USVs,
                                   can_be_stopped=False)
        model.spectrogram_model.background_task = task


def make_frequency_classification(model: MainModel, callback: Callable):

    threshold = model.settings_model.threshold_model.threshold
    low_label = model.settings_model.threshold_model.label_low
    high_label = model.settings_model.threshold_model.label_high
    spec_data = model.spectrogram_model.spectrogram_data

    # We purposefully make shallow copy here. This way we can iterate over
    # the same annotation list as we have at the beginning od classification
    # even if the original list changes in the meantime. At the same time
    # we are able to edit original annotation content.
    annotations = copy.copy(model.spectrogram_model.annotation_table_model.annotations)
    classified_squeaks = classify_USVs(
        spec=spec_data,
        squeak_boxes=[
            annotation.to_squeak_box(spec_data) for annotation in annotations
        ],
        threshold=float(threshold),
        low_label=low_label,
        high_label=high_label,
        callback=callback,
    )

    for annotation, squeak_box in zip(annotations, classified_squeaks):
        annotation.label = squeak_box.label

    model.spectrogram_model.annotation_table_model.update_selected_column(4)  # USV TYPE
