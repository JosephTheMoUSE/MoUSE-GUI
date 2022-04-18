import logging
import warnings

from PySide6 import QtWidgets, QtCore
from mouseapp.controller.settings_controllers import common_settings_controller
from mouseapp.model.main_models import MainModel
from mouseapp.view import utils
from mouseapp.view.classification_settings_view import ClassificationSettingsWindow
from mouseapp.view.denoising_settings_view import DenoisingSettingsWindow
from mouseapp.view.detection_settings_view import DetectionSettingsWindow
from mouseapp.view.filtering_settings_view import FilteringSettingsWindow
from mouseapp.view.generated.settings.ui_settings import Ui_SettingsWidget


class SettingsWindow(QtWidgets.QWidget, Ui_SettingsWidget):
    """Settings window class."""

    def __init__(self, model: MainModel):
        super(SettingsWindow, self).__init__()
        self.setupUi(self)
        self.model = model

        # Makes the new window stay on top of the application
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        # enforce garbage collection of this window
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Instantiate denoising settings widget
        self.denoising_widget = utils.initialize_widget(DenoisingSettingsWindow(model))
        utils.initialize_basic_layout(self.denoisingTab, self.denoising_widget)

        # Instantiate detection settings widget
        self.detection_widget = utils.initialize_widget(DetectionSettingsWindow(model))
        utils.initialize_basic_layout(self.detectionTab, self.detection_widget)

        # Instantiate filtering settings widget
        self.filtering_widget = utils.initialize_widget(FilteringSettingsWindow(model))
        utils.initialize_basic_layout(self.filteringTab, self.filtering_widget)

        # Instantiate classification settings widget
        self.classification_widget = utils.initialize_widget(
            ClassificationSettingsWindow(model))
        utils.initialize_basic_layout(self.classificationTab,
                                      self.classification_widget)

        # Set values on every settings widget
        logging.debug("[SettingsWindow] Call "
                      "`common_settings_controller.emit_settings_signals`")
        common_settings_controller.emit_settings_signals(self.model)

        self.settingsCatrgories.currentChanged.connect(
            lambda id: self._on_current_tab_changed(id))

    def closeEvent(self, event):
        self.detection_widget.closeEvent(event)
        event.accept()

    def _on_current_tab_changed(self, id):
        if id == 0:
            self.denoising_widget.change_denoising_page(
                self.denoising_widget.denoisingComboBox.currentText())
        elif id == 1:
            self.detection_widget.change_detection_page(
                self.detection_widget.detectionComboBox.currentText())
        elif id == 2:
            pass
        elif id == 3:
            pass
        else:
            warnings.warn(f"Tab: {id} not supported")
