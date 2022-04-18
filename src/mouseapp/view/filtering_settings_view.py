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

        # signals
        self.model.settings_model.filtering_model.frequency_filter_changed.connect(
            self._on_frequency_filter_signal)
        self.model.settings_model.filtering_model.frequency_threshold_changed.connect(
            self._on_frequency_threshold_signal)

        model.settings_model.filtering_model.emit_all_setting_signals()

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
