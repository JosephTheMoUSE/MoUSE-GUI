from typing import Optional

from PySide6 import QtWidgets
from mouse.utils import visualization
from mouse.utils.sound_util import SpectrogramData
from mouseapp.model.main_models import MainModel
from mouseapp.view import widgets
from mouseapp.view.generated.settings.ui_preview_settings import \
    Ui_PreviewSettingsWidget


class PreviewSettingsWindow(QtWidgets.QWidget, Ui_PreviewSettingsWidget):
    """Preview settings window class."""

    def __init__(self, model: MainModel, use_only_upper=False):
        super(PreviewSettingsWindow, self).__init__()
        self.setupUi(self)
        self.model = model
        self.use_only_upper = use_only_upper

        # method preview
        if use_only_upper:
            self.canvas = widgets.Canvas(1)
            self.upper_axis = self.canvas.figure.axes[0]
            self.verticalLayout.addWidget(self.canvas)
        else:
            self.canvas = widgets.Canvas(2, sharex=True)
            self.upper_axis = self.canvas.figure.axes[0]
            self.lower_axis = self.canvas.figure.axes[1]
            self.verticalLayout.addWidget(self.canvas)

        # signals
        self.model.settings_model.time_start_changed. \
            connect(self._on_start_signal)
        self.model.settings_model.time_end_changed.connect(self._on_end_signal)

    def draw_upper_spect(self, value: Optional[SpectrogramData]):
        self.upper_axis.clear()
        visualization.draw_spectrogram(spec=value, ax=self.upper_axis)
        if not self.use_only_upper:
            self.upper_axis.set_xlabel(None)
        self.canvas.draw()

    def draw_lower_spect(self, value: Optional[SpectrogramData]):
        self.lower_axis.clear()
        visualization.draw_spectrogram(spec=value, ax=self.lower_axis)
        self.canvas.draw()

    def _on_start_signal(self, value: float):
        self.previewStartLineEdit.setText(str(value))

    def _on_end_signal(self, value: float):
        self.previewEndLineEdit.setText(str(value))
