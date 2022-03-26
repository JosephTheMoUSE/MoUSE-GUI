import logging
from typing import Optional, List

import matplotlib.pyplot as plt
import numpy as np
from PySide6 import QtWidgets, QtCore
from mouse.utils import visualization
from mouse.utils.data_util import SqueakBox
from mouse.utils.sound_util import SpectrogramData
from mouseapp.controller.detection_controller import set_detection_method
from mouseapp.controller.settings_controllers import (
    gac_settings_controller,
    common_settings_controller,
    neural_settings_controller,
)
from mouseapp.model.main_models import MainModel
from mouseapp.model.settings.utils import Detection
from mouseapp.view import utils
from mouseapp.view.generated.settings.ui_detection_settings import (
    Ui_DetectionSettingsWidget,)
from mouseapp.view.preview_settings_view import PreviewSettingsWindow
from mouseapp.view.widgets import SliderWithEdit


class DetectionSettingsWindow(QtWidgets.QWidget, Ui_DetectionSettingsWidget):
    """Detection settings window class."""

    def __init__(self, model: MainModel):
        super(DetectionSettingsWindow, self).__init__()
        self.setupUi(self)
        self.model = model
        self.rectangles: List[plt.Rectangle] = []
        self.was_gac_loaded = False

        # enforce garbaga collection of this window
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.gac_preview = PreviewSettingsWindow(self.model)
        self.nn_preview = PreviewSettingsWindow(self.model, use_only_upper=True)
        self.gac_preview.hide()
        self.nn_preview.hide()
        self.verticalLayout.addWidget(self.gac_preview)
        self.verticalLayout.addWidget(self.nn_preview)

        # Change `QSlider` to `SliderWithEdit`
        self.floodLevelSlider = utils.initialize_widget(
            SliderWithEdit(minimum=0, maximum=1, resolution=100))
        self.gacGridLayout.replaceWidget(self.placeholderFloodLevelSlider,
                                         self.floodLevelSlider)
        self.placeholderFloodLevelSlider.deleteLater()
        self.baloonSlider = utils.initialize_widget(
            SliderWithEdit(minimum=0, maximum=1, resolution=100))
        self.gacGridLayout.replaceWidget(self.placeholderBaloonSlider,
                                         self.baloonSlider)
        self.placeholderBaloonSlider.deleteLater()

        # connect inputs
        # # connect detection inputs
        self.detectionComboBox.currentTextChanged.connect(self.change_detection_page)
        self.gac_preview.runPreviewButton.clicked.connect(self._on_run_detection)
        self.nn_preview.runPreviewButton.clicked.connect(self._on_run_detection)

        # # connect GAC inputs
        self.baloonComboBox.currentTextChanged.connect(self._on_baloon_combobox)
        self.iterationsLineEdit.editingFinished.connect(self._on_iterations_edit)
        self.smoothingLineEdit.editingFinished.connect(self._on_smoothing_edit)
        self.sigmaLineEdit.editingFinished.connect(self._on_sigma_edit)
        self.alphaLineEdit.editingFinished.connect(self._on_alpha_edit)
        self.baloonSlider.modifications_finished.connect(self._on_threshold_edit)
        self.floodLevelSlider.modifications_finished.connect(self._on_flood_changed)
        self.restoreGACButton.clicked.connect(self._on_gac_restore)
        self.gac_preview.previewButton.clicked.connect(self._on_preview_time)
        self.nn_preview.previewButton.clicked.connect(self._on_preview_time)

        # Neural Network inputs
        self.modelTypeComboBox.currentTextChanged.connect(self._model_name_changed)
        self.batchSizeSpinBox.valueChanged.connect(self._batch_size_changed)
        self.confidenceSpinBox.valueChanged.connect(self._confidence_value_changed)

        # connect signals
        self.model.settings_model.detection_spec_changed.connect(
            self.gac_preview.draw_upper_spect)
        self.model.settings_model.detection_spec_changed.connect(
            self.nn_preview.draw_upper_spect)
        self.model.settings_model.chosen_detection_method_signal.connect(
            self.change_detection_method)
        self._connect_nn_signals()
        self._connect_gac_signals()

        self.preview_redrawed = False

        logging.debug("[DetectionSettingsWindow] Finished initialization")

    def closeEvent(self, event):
        if self.detectionStackedWidget.currentWidget() == self.GACPage:
            gac_settings_controller.stop_gac(self.model)
        elif self.detectionStackedWidget.currentWidget() == self.nnPage:
            neural_settings_controller.stop_nn(self.model)

    def change_detection_method(self, text: str):
        text_map = {
            Detection.GAC: 0,
            Detection.NN: 1,
        }
        self.detectionComboBox.setCurrentIndex(text_map[text])
        self.change_detection_page(text)

    def change_detection_page(self, text: str):
        self.gac_preview.hide()
        self.nn_preview.hide()

        if "gac" in text.lower():
            self.detectionStackedWidget.setCurrentWidget(self.GACPage)

            if not self.was_gac_loaded:
                gac_settings_controller.emit_settings_signals(self.model)
                self.was_gac_loaded = True
            else:
                gac_settings_controller.emit_detections(self.model)

            set_detection_method(self.model, Detection.GAC)
            self.gac_preview.show()
            if self.preview_redrawed:
                self.preview_redrawed = False
                self._on_preview_time()
        elif "nn detector" in text.lower():
            self.detectionStackedWidget.setCurrentWidget(self.nnPage)
            neural_settings_controller.emit_settings_signals(self.model)
            neural_settings_controller.set_NN_preview(self.model)
            set_detection_method(self.model, Detection.NN)
            self.nn_preview.show()

    def _connect_gac_signals(self):
        self.model.settings_model.gac_model.sigma_changed.connect(self._on_sigma_signal)
        self.model.settings_model.gac_model.alpha_changed.connect(self._on_alpha_signal)
        self.model.settings_model.gac_model.iterations_changed.connect(
            self._on_iterations_signal)
        self.model.settings_model.gac_model.smoothing_changed.connect(
            self._on_smoothing_signal)
        self.model.settings_model.gac_model.threshold_changed.connect(
            self._on_threshold_signal)
        self.model.settings_model.gac_model.balloon_changed.connect(
            self._on_baloon_signal)
        self.model.settings_model.gac_model.flood_threshold_changed.connect(
            self._on_flood_signal)
        self.model.settings_model.gac_model.preview_model.preview_changed.connect(
            self._on_gac_preview_signal)
        self.model.settings_model.gac_model.preview_model.detections_changed.connect(
            self._on_gac_detection_signal)
        self.model.settings_model.gac_model.preview_model.method_allowed_changed.connect(
            self._on_method_allowed_signal)

    def _connect_nn_signals(self):
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

    def _on_baloon_combobox(self, text: str):
        gac_settings_controller.set_baloon(model=self.model, value=text)

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

    def _on_preview_time(self):

        if self.detectionStackedWidget.currentWidget() == self.GACPage:
            common_settings_controller.set_preview_start(
                model=self.model, value=self.gac_preview.previewStartLineEdit.text())
            common_settings_controller.set_preview_end(
                model=self.model, value=self.gac_preview.previewEndLineEdit.text())
            gac_settings_controller.set_gac_preview(self.model)
        elif self.detectionStackedWidget.currentWidget() == self.nnPage:
            self.preview_redrawed = True
            common_settings_controller.set_preview_start(
                model=self.model, value=self.nn_preview.previewStartLineEdit.text())
            common_settings_controller.set_preview_end(
                model=self.model, value=self.nn_preview.previewEndLineEdit.text())
            neural_settings_controller.set_NN_preview(self.model)

    def _on_run_detection(self):
        if self.detectionStackedWidget.currentWidget() == self.GACPage:
            gac_settings_controller.run_preview_GAC(self.model)
        elif self.detectionStackedWidget.currentWidget() == self.nnPage:
            neural_settings_controller.run_preview_NN(self.model)

    def _on_baloon_signal(self, value: float):
        if value > 0:
            self.baloonComboBox.setCurrentText("positive")
        elif value < 0:
            self.baloonComboBox.setCurrentText("negative")
        else:
            self.baloonComboBox.setCurrentText("none")

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
        self.baloonSlider.set_value(value)

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
        if level_set is not None:
            img = np.ma.array(data=level_set, mask=level_set)
            self.gac_preview.lower_axis.pcolormesh(img, cmap="gray")
        self.gac_preview.canvas.draw()

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
