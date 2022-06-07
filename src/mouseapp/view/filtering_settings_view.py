from PySide6 import QtCore, QtWidgets

from mouseapp.controller.settings_controllers import filtering_settings_controller
from mouseapp.model.main_models import MainModel
from mouseapp.view.generated.settings.ui_filtering_settings import (
    Ui_FilteringSettingsWidget,)


class FilteringSettingsWindow(QtWidgets.QWidget, Ui_FilteringSettingsWidget):
    """Detection filtering settings window class."""

    def __init__(self, model: MainModel):
        super(FilteringSettingsWindow, self).__init__()
        self.setupUi(self)
        self.model = model

        # enforce garbage collection of this window
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        # inputs
        self.frequencyThresholdNameEdit.setEnabled(False)
        self.frequencyFilterCheckBox.stateChanged.connect(
            self._on_frequency_filter_checked)
        self.frequencyThresholdNameEdit.editingFinished.connect(
            self._on_frequency_threshold_edited)
        self.batchSizeSpinBox.setEnabled(False)
        self.confidenceSpinBox.setEnabled(False)
        self.modelTypeComboBox.setEnabled(False)
        self.neuralNetworkFilterCheckBox.stateChanged.connect(
            self._on_neural_network_filter_checked)
        self.modelTypeComboBox.currentTextChanged.connect(self._model_name_changed)
        self.batchSizeSpinBox.valueChanged.connect(self._batch_size_changed)
        self.confidenceSpinBox.valueChanged.connect(self._confidence_value_changed)

        # signals
        self.model.settings_model.filtering_model.frequency_filter_changed.connect(
            self._on_frequency_filter_signal)
        self.model.settings_model.filtering_model.frequency_threshold_changed.connect(
            self._on_frequency_threshold_signal)
        self.model.settings_model.filtering_model.neural_network_filter_changed.connect(
            self._on_neural_network_filter_signal)
        self.model.settings_model.filtering_model.model_batch_size_changed.connect(
            self._on_batch_signal)
        self.model.settings_model.filtering_model.model_name_changed.connect(
            self._on_model_name_signal)
        self.model.settings_model.filtering_model.model_confidence_threshold_changed.connect(
            self._on_confidence_threshold_signal)

        model.settings_model.filtering_model.emit_all_setting_signals()

    # Frequency filtering
    def _on_frequency_filter_checked(self):
        self.frequencyThresholdNameEdit.setEnabled(
            self.frequencyFilterCheckBox.isChecked())
        filtering_settings_controller.set_frequency_filter(
            self.model, self.frequencyFilterCheckBox.isChecked())

    def _on_frequency_threshold_edited(self):
        filtering_settings_controller.set_frequency_threshold(
            self.model, self.frequencyThresholdNameEdit.text())

    def _on_frequency_filter_signal(self, value):
        if value:
            self.frequencyFilterCheckBox.setCheckState(QtCore.Qt.Checked)
            self.frequencyThresholdNameEdit.setEnabled(True)
        else:
            self.frequencyFilterCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.frequencyThresholdNameEdit.setEnabled(False)

    def _on_frequency_threshold_signal(self, value):
        self.frequencyThresholdNameEdit.setText(str(value))

    # Neural network filtering
    def _on_neural_network_filter_checked(self):
        self.batchSizeSpinBox.setEnabled(self.neuralNetworkFilterCheckBox.isChecked())
        self.confidenceSpinBox.setEnabled(self.neuralNetworkFilterCheckBox.isChecked())
        self.modelTypeComboBox.setEnabled(self.neuralNetworkFilterCheckBox.isChecked())
        filtering_settings_controller.set_neural_network_filter(
            self.model, self.neuralNetworkFilterCheckBox.isChecked())

    def _on_neural_network_filter_signal(self, value):
        if value:
            self.neuralNetworkFilterCheckBox.setCheckState(QtCore.Qt.Checked)
            self.batchSizeSpinBox.setEnabled(True)
            self.confidenceSpinBox.setEnabled(True)
            self.modelTypeComboBox.setEnabled(True)
        else:
            self.neuralNetworkFilterCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.batchSizeSpinBox.setEnabled(False)
            self.confidenceSpinBox.setEnabled(False)
            self.modelTypeComboBox.setEnabled(False)

    def _on_batch_signal(self, val):
        self.batchSizeSpinBox.setValue(val)

    def _on_confidence_threshold_signal(self, val):
        self.confidenceSpinBox.setValue(int(val * 100))

    def _on_model_name_signal(self, val):
        self.modelTypeComboBox.setCurrentText(val)

    def _model_name_changed(self, model_name: str):
        filtering_settings_controller.set_model_name(self.model, model_name)

    def _batch_size_changed(self, batch_size: int):
        filtering_settings_controller.set_batch_size(self.model, batch_size)

    def _confidence_value_changed(self, confidence: int):
        filtering_settings_controller.set_confidence_threshold(self.model, confidence)
