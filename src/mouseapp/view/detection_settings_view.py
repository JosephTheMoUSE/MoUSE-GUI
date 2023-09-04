import logging
from typing import Optional, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from PySide6 import QtWidgets, QtCore

import mouseapp.controller.settings_controllers.gac_optimisation_controller
from mouse.utils import visualization
from mouse.utils.data_util import SqueakBox
from mouse.utils.sound_util import SpectrogramData
from mouseapp.controller.detection_controller import set_detection_method
from mouseapp.controller.settings_controllers import (
    gac_settings_controller,
    common_settings_controller,
    neural_settings_controller,
    gac_optimisation_controller,
)
from mouseapp.controller.utils import warn_user
from mouseapp.model.main_models import MainModel
from mouseapp.model.settings.utils import Detection, Denoising, OptimisationResult
from mouseapp.view import utils
from mouseapp.view.generated.settings.ui_detection_settings import (
    Ui_DetectionSettingsWidget,)
from mouseapp.view.preview_settings_view import PreviewSettingsWindow
from mouseapp.view.widgets import SliderWithEdit, TaskProgressbar


class DetectionSettingsWindow(QtWidgets.QWidget, Ui_DetectionSettingsWidget):
    """Detection settings window class."""

    def __init__(self, model: MainModel):
        super(DetectionSettingsWindow, self).__init__()
        self.setupUi(self)
        self.model = model
        self.rectangles: List[plt.Rectangle] = []
        self.was_gac_loaded = False
        self.progressbar: Optional[TaskProgressbar] = None

        # enforce garbage collection of this window
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.gac_preview = PreviewSettingsWindow(self.model)
        self.nn_preview = PreviewSettingsWindow(self.model, use_only_upper=True)
        self.GACPreviewLayout.addWidget(self.gac_preview)
        self.nnPreviewLayout.addWidget(self.nn_preview)

        self.replace_slider_placeholders()

        # connect inputs
        self.detectionComboBox.currentTextChanged.connect(self.change_detection_page)
        self._connect_nn_inputs()
        self._connect_gac_inputs()
        self._connect_optimisation_inputs()

        # connect signals
        self.model.settings_model.chosen_detection_method_signal.connect(
            self.change_detection_method)
        self._connect_nn_signals()
        self._connect_gac_signals()
        self._connect_optimisation_signals()

        self.time_changed = False

        logging.debug("[DetectionSettingsWindow] Finished initialization")

    def replace_slider_placeholders(self):
        """Change `QSlider` to `SliderWithEdit`."""
        self.floodLevelSlider = utils.initialize_widget(
            SliderWithEdit(minimum=0, maximum=1, resolution=100))
        self.gacGridLayout.replaceWidget(self.placeholderFloodLevelSlider,
                                         self.floodLevelSlider)
        self.placeholderFloodLevelSlider.deleteLater()
        self.balloonSlider = utils.initialize_widget(
            SliderWithEdit(minimum=0, maximum=1, resolution=100))
        self.gacGridLayout.replaceWidget(self.placeholderBalloonSlider,
                                         self.balloonSlider)
        self.placeholderBalloonSlider.deleteLater()

    def _connect_gac_inputs(self):
        self.gac_preview.runPreviewButton.clicked.connect(self._on_run_detection)
        self.balloonComboBox.currentTextChanged.connect(self._on_balloon_combobox)
        self.iterationsLineEdit.editingFinished.connect(self._on_iterations_edit)
        self.smoothingLineEdit.editingFinished.connect(self._on_smoothing_edit)
        self.sigmaLineEdit.editingFinished.connect(self._on_sigma_edit)
        self.alphaLineEdit.editingFinished.connect(self._on_alpha_edit)
        self.balloonSlider.modifications_finished.connect(self._on_threshold_edit)
        self.floodLevelSlider.modifications_finished.connect(self._on_flood_changed)
        self.restoreGACButton.clicked.connect(self._on_gac_restore)
        self.gac_preview.previewButton.clicked.connect(self._on_preview_time)
        self.nn_preview.previewButton.clicked.connect(self._on_preview_time)

    def _connect_optimisation_inputs(self):
        self.runOptimisationPushButton.clicked.connect(self._on_gac_optimisation)
        self.automaticGACConfigurationButton.clicked.connect(self._on_autoconfigure_gac)
        self.timeStartLineEdit.editingFinished.connect(self._on_optimisation_time_start)
        self.timeEndLineEdit.editingFinished.connect(self._on_optimisation_time_end)
        self.numTrialsLineEdit.editingFinished.connect(self._on_optimisation_iters)
        self.randomTrialsLineEdit.editingFinished.connect(
            self._on_optimisation_random_iters)
        self.betaLineEdit.editingFinished.connect(self._on_optimisation_beta)
        self.metricComboBox.currentTextChanged.connect(self._on_optimisation_metric)

    def _connect_nn_inputs(self):
        self.nn_preview.runPreviewButton.clicked.connect(self._on_run_detection)
        self.modelTypeComboBox.currentTextChanged.connect(self._model_name_changed)
        self.batchSizeSpinBox.valueChanged.connect(self._batch_size_changed)
        self.confidenceSpinBox.valueChanged.connect(self._confidence_value_changed)

    def closeEvent(self, event):
        if self.detectionStackedWidget.currentWidget() == self.GACPage:
            gac_settings_controller.stop_gac(self.model)
        elif self.detectionStackedWidget.currentWidget() == self.nnPage:
            neural_settings_controller.stop_nn(self.model)

    def change_detection_method(self, text: str):
        text_map = {
            Detection.GAC: 0,
            Detection.NN: 2,
        }
        self.detectionComboBox.setCurrentIndex(text_map[text])
        self.change_detection_page(text)

    def change_detection_page(self, text: str):
        if "gac" == text.lower():
            self.detectionStackedWidget.setCurrentWidget(self.GACPage)

            if not self.was_gac_loaded:
                gac_settings_controller.emit_settings_signals(self.model)
                self.was_gac_loaded = True
            else:
                gac_settings_controller.emit_detections(self.model)

            set_detection_method(self.model, Detection.GAC)
            if self.time_changed:
                self.time_changed = False
                self._on_preview_time()
        elif "gac optimisation" == text.lower():
            self.detectionStackedWidget.setCurrentWidget(self.GACOptimisationPage)
        elif "nn detector" in text.lower():
            if self.model.settings_model.chosen_denoising_method != Denoising.NO_FILTER:
                warn_user(
                    self.model,
                    "Neural Network wasn't prepared for a denoised spectrogram! Quality of detected USVs may be low.",
                )

            self.detectionStackedWidget.setCurrentWidget(self.nnPage)
            neural_settings_controller.emit_settings_signals(self.model)
            neural_settings_controller.set_NN_preview(self.model)
            set_detection_method(self.model, Detection.NN)

    def _connect_gac_signals(self):
        self.model.settings_model.detection_spec_changed.connect(
            self.gac_preview.draw_upper_spect)
        self.model.settings_model.gac_model.sigma_changed.connect(self._on_sigma_signal)
        self.model.settings_model.gac_model.alpha_changed.connect(self._on_alpha_signal)
        self.model.settings_model.gac_model.iterations_changed.connect(
            self._on_iterations_signal)
        self.model.settings_model.gac_model.smoothing_changed.connect(
            self._on_smoothing_signal)
        self.model.settings_model.gac_model.threshold_changed.connect(
            self._on_threshold_signal)
        self.model.settings_model.gac_model.balloon_changed.connect(
            self._on_balloon_signal)
        self.model.settings_model.gac_model.flood_threshold_changed.connect(
            self._on_flood_signal)
        self.model.settings_model.gac_model.preview_model.preview_changed.connect(
            self._on_gac_preview_signal)
        self.model.settings_model.gac_model.preview_model.detections_changed.connect(
            self._on_gac_detection_signal)
        self.model.settings_model.gac_model.preview_model.method_allowed_changed.connect(
            self._on_method_allowed_signal)

    def _connect_optimisation_signals(self):
        self.model.settings_model.gac_model.optimisation_results_changed.connect(
            self._on_optimisation_results_signal)
        self.model.settings_model.gac_model.optimisation_box_count_changed.connect(
            self._on_optimisation_box_count_signal)
        self.model.settings_model.gac_model.optimisation_best_changed.connect(
            self._on_optimisation_best_signal)
        self.model.settings_model.gac_model.time_start_changed.connect(
            self._on_time_start_signal)
        self.model.settings_model.gac_model.time_end_changed.connect(
            self._on_time_end_signal)
        self.model.settings_model.gac_model.beta_changed.connect(self._on_beta_signal)
        self.model.settings_model.gac_model.optimisation_iters_changed.connect(
            self._on_optimisation_iters_signal)
        self.model.settings_model.gac_model.optimisation_random_iters_changed.connect(
            self._on_optimisation_random_iters_signal)
        self.model.settings_model.gac_model.progressbar_changed.connect(
            self._on_progressbar_definition)
        self.model.settings_model.gac_model.progressbar_info_changed.connect(
            self._on_progressbar_info_changed)
        self.model.settings_model.gac_model.optimisation_allowed_changed.connect(
            self._on_optimisation_allowed_changed)

    def _connect_nn_signals(self):
        self.model.settings_model.detection_spec_changed.connect(
            self.nn_preview.draw_upper_spect)
        self.model.settings_model.nn_model.model_batch_size_changed.connect(
            self._on_batch_signal)
        self.model.settings_model.nn_model.model_confidence_threshold_changed.connect(
            self._on_confidence_threshold_signal)
        self.model.settings_model.nn_model.model_name_changed.connect(
            self._on_model_name_signal)

        self.model.settings_model.nn_model.preview_model.detections_changed.connect(
            self._on_nn_detection_signal)
        self.model.settings_model.nn_model.preview_model.method_allowed_changed.connect(
            self._on_method_allowed_signal)

    def _on_balloon_combobox(self, text: str):
        gac_settings_controller.set_balloon(model=self.model, value=text)

    def _on_threshold_edit(self, value: int):
        gac_settings_controller.set_threshold(model=self.model, value=value)

    def _on_smoothing_edit(self):
        gac_settings_controller.set_smoothing(model=self.model,
                                              value=int(self.smoothingLineEdit.text()))

    def _on_sigma_edit(self):
        gac_settings_controller.set_sigma(model=self.model,
                                          value=self.sigmaLineEdit.text())

    def _on_alpha_edit(self):
        gac_settings_controller.set_alpha(model=self.model,
                                          value=self.alphaLineEdit.text())

    def _on_flood_changed(self, value: int):
        gac_settings_controller.set_flood_threshold(model=self.model, value=value)

    def _on_iterations_edit(self):
        gac_settings_controller.set_iterations(model=self.model,
                                               value=int(
                                                   self.iterationsLineEdit.text()))

    def _on_gac_restore(self):
        gac_settings_controller.restore_default_gac_values(self.model)

    def _on_gac_optimisation(self):
        gac_optimisation_controller.run_optimisation(self.model)

    def _on_autoconfigure_gac(self):
        gac_optimisation_controller.autoconfigure_gac(self.model)

    def _on_optimisation_time_start(self):
        mouseapp.controller.settings_controllers.gac_optimisation_controller.set_optimisation_time_start(
            model=self.model, value=self.timeStartLineEdit.text())

    def _on_optimisation_time_end(self):
        mouseapp.controller.settings_controllers.gac_optimisation_controller.set_optimisation_time_end(
            model=self.model, value=self.timeEndLineEdit.text())

    def _on_optimisation_iters(self):
        mouseapp.controller.settings_controllers.gac_optimisation_controller.set_optimisation_iters(
            model=self.model, value=self.numTrialsLineEdit.text())

    def _on_optimisation_random_iters(self):
        mouseapp.controller.settings_controllers.gac_optimisation_controller.set_optimisation_random_iters(
            model=self.model, value=self.randomTrialsLineEdit.text())

    def _on_optimisation_beta(self):
        mouseapp.controller.settings_controllers.gac_optimisation_controller.set_beta(
            model=self.model, value=self.betaLineEdit.text())

    def _on_optimisation_metric(self, value: str):
        mouseapp.controller.settings_controllers.gac_optimisation_controller.set_metric(
            model=self.model, value=value)

    def _on_preview_time(self):

        if self.detectionStackedWidget.currentWidget() == self.GACPage:
            if common_settings_controller.set_preview_start_end(
                    model=self.model,
                    prev_start=self.gac_preview.previewStartLineEdit.text(),
                    prev_end=self.gac_preview.previewEndLineEdit.text()):
                gac_settings_controller.set_gac_preview(self.model)
        elif self.detectionStackedWidget.currentWidget() == self.nnPage:
            self.time_changed = True
            if common_settings_controller.set_preview_start_end(
                    model=self.model,
                    prev_start=self.nn_preview.previewStartLineEdit.text(),
                    prev_end=self.nn_preview.previewEndLineEdit.text()):
                neural_settings_controller.set_NN_preview(self.model)

    def _on_run_detection(self):
        if self.detectionStackedWidget.currentWidget() == self.GACPage:
            gac_settings_controller.run_preview_GAC(self.model)
        elif self.detectionStackedWidget.currentWidget() == self.nnPage:
            neural_settings_controller.run_preview_NN(self.model)

    def _on_balloon_signal(self, value: float):
        if value > 0:
            self.balloonComboBox.setCurrentText("positive")
        elif value < 0:
            self.balloonComboBox.setCurrentText("negative")
        else:
            self.balloonComboBox.setCurrentText("none")

    def _on_sigma_signal(self, value: float):
        gac_settings_controller.set_gac_preview(self.model)
        self.sigmaLineEdit.setText(str(value))

    def _on_alpha_signal(self, value: float):
        gac_settings_controller.set_gac_preview(self.model)
        self.alphaLineEdit.setText(str(value))

    def _on_iterations_signal(self, value: int):
        self.iterationsLineEdit.setText(str(value))

    def _on_smoothing_signal(self, value: int):
        self.smoothingLineEdit.setText(str(value))

    def _on_threshold_signal(self, value: float):
        self.balloonSlider.set_value(value)

    def _on_flood_signal(self, value: float):
        gac_settings_controller.set_gac_preview(self.model)
        self.floodLevelSlider.set_value(value)

    def _on_start_signal(self, value: float):
        self.previewStartLineEdit.setText(str(value))

    def _on_end_signal(self, value: float):
        self.previewEndLineEdit.setText(str(value))

    def _on_gac_preview_signal(self,
                               value: [Optional[SpectrogramData],
                                       Optional[np.ndarray]]):
        spec, level_set = value
        self.gac_preview.lower_axis.clear()
        visualization.draw_spectrogram(spec=spec,
                                       ax=self.gac_preview.lower_axis,
                                       vmin=0.0,
                                       vmax=1.0)
        self.gac_preview.lower_axis.set_ylabel(f"~GAC steps~\n{self.gac_preview.lower_axis.get_ylabel()}")
        if level_set is not None:
            img = np.ma.array(data=level_set, mask=level_set)
            self.gac_preview.lower_axis.pcolormesh(img, cmap="gray")
        self.gac_preview.canvas.draw()

    def _on_optimisation_results_signal(self, value: List[OptimisationResult]):
        if len(value) > 0:
            last_results = sorted([round(result.metric, 2) for result in value])[-5:]
            best = str(self.model.settings_model.gac_model.optimisation_best)

            self.resultLabel.setText(f"Best results: {last_results}\n\n"
                                     f"Best result:\n{best}")

    def _on_optimisation_box_count_signal(self, value: int):
        self.USVNumLabel.setText(f"Number of USVs used in optimisation: {value}")

    def _on_optimisation_best_signal(self, value: Optional[OptimisationResult]):
        if isinstance(value, OptimisationResult):
            self.automaticGACConfigurationButton.setEnabled(True)
        else:
            self.automaticGACConfigurationButton.setDisabled(True)

    def _on_time_start_signal(self, value: float):
        self.timeStartLineEdit.setText(str(value))

    def _on_time_end_signal(self, value: float):
        self.timeEndLineEdit.setText(str(value))

    def _on_beta_signal(self, value: float):
        self.betaLineEdit.setText(str(value))

    def _on_optimisation_iters_signal(self, value: int):
        self.numTrialsLineEdit.setText(str(value))

    def _on_optimisation_random_iters_signal(self, value: int):
        self.randomTrialsLineEdit.setText(str(value))

    def _on_batch_signal(self, val):
        self.batchSizeSpinBox.setValue(val)

    def _on_confidence_threshold_signal(self, val):
        self.confidenceSpinBox.setValue(int(val * 100))

    def _on_model_name_signal(self, val):
        self.modelTypeComboBox.setCurrentText(val)

    def _model_name_changed(self, model_name: str):
        neural_settings_controller.set_model_name(self.model, model_name)

    def _batch_size_changed(self, batch_size: int):
        neural_settings_controller.set_batch_size(self.model, batch_size)

    def _confidence_value_changed(self, confidence: int):
        neural_settings_controller.set_confidence_threshold(self.model, confidence)

    def _on_method_allowed_signal(self, value: bool):
        self.gac_preview.runPreviewButton.setEnabled(value)
        self.nn_preview.runPreviewButton.setEnabled(value)

    def _on_gac_detection_signal(self, value: [List[SqueakBox], int]):
        boxes, height = value
        for rect in self.rectangles:
            rect.remove()
        self.rectangles = visualization.draw_boxes(boxes=boxes,
                                                   spec_height=height,
                                                   ax=self.gac_preview.upper_axis)
        self.gac_preview.canvas.draw()

    def _on_nn_detection_signal(self, value: [List[SqueakBox], int]):
        boxes, height = value
        for rect in self.rectangles:
            rect.remove()
        self.rectangles = visualization.draw_boxes(boxes=boxes,
                                                   spec_height=height,
                                                   ax=self.nn_preview.upper_axis)
        self.nn_preview.canvas.draw()

    def _on_progressbar_definition(self, defined: bool):
        if not defined:
            self.progressbarPlaceholderLayout.removeWidget(self.progressbar)
            self.progressbar.deleteLater()
            self.progressbar = None
            return

        if self.model.settings_model.gac_model.background_task is None:
            raise ValueError("Progress bar is associated with "
                             "`background_task`, but `background_task` is "
                             "`None`.")
        killable = self.model.settings_model.gac_model.background_task.is_killable()
        self.progressbar: TaskProgressbar = utils.initialize_widget(
            TaskProgressbar(hide_stop_button=not killable))
        if killable:
            self.progressbar.buttonClicked.connect(
                self.model.settings_model.gac_model.background_task.kill)

        self.progressbarPlaceholderLayout.addWidget(self.progressbar)

    def _on_progressbar_info_changed(self, values: Tuple):
        left, progress, right = values
        self.progressbar.set_values(left_txt=left, progress=progress, right_txt=right)

    def _on_optimisation_allowed_changed(self, value: bool):
        self.runOptimisationPushButton.setEnabled(value)
