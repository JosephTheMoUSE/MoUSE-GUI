import logging

from PySide6 import QtWidgets, QtCore

from mouseapp.controller.settings_controllers import classification_controller
from mouseapp.model.main_models import MainModel
from mouseapp.view.generated.settings.ui_classification_settings import \
    Ui_ClassificationSettingsWidget


class ClassificationSettingsWindow(QtWidgets.QWidget,
                                   Ui_ClassificationSettingsWidget):
    """Classification settings window class."""

    def __init__(self, model: MainModel):
        super(ClassificationSettingsWindow, self).__init__()
        self.setupUi(self)
        self.model = model

        # enforce garbaga collection of this window
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Connect inputs
        self.frequencyThresholdEdit.editingFinished.connect(
            lambda: classification_controller.set_frequency_threshold(
                model=self.model,
                threshold_txt=self.frequencyThresholdEdit.text()))
        self.lowLabelNameEdit.editingFinished.connect(
            lambda: classification_controller.set_low_freq_label(
                model=self.model, label=self.lowLabelNameEdit.text()))
        self.highLabelNameEdit.editingFinished.connect(
            lambda: classification_controller.set_high_freq_label(
                model=self.model, label=self.highLabelNameEdit.text()))

        # Connect signals
        model.settings_model.threshold_model.threshold_changed.connect(
            self.on_frequency_threshold_changed)
        model.settings_model.threshold_model.low_label_changed.connect(
            self.on_low_label_name_changed)
        model.settings_model.threshold_model.high_label_changed.connect(
            self.on_high_label_name_changed)

        model.settings_model.threshold_model.emit_all_setting_signals()
        logging.debug("[ClassificationSettingsWindow] Finished initialization")

    def on_frequency_threshold_changed(self, x):
        self.frequencyThresholdEdit.setText(str(x))

    def on_low_label_name_changed(self, x):
        self.lowLabelNameEdit.setText(str(x))

    def on_high_label_name_changed(self, x):
        self.highLabelNameEdit.setText(str(x))
