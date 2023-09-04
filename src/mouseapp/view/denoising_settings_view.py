import logging
import warnings
from functools import partial
from pathlib import Path

from PySide6 import QtWidgets, QtCore
from mouseapp.controller.settings_controllers import (
    bilateral_settings_controller,
    no_filter_settings_controller,
    sdts_settings_controller,
    noise_gate_settings_controller,
    common_settings_controller,
)
from mouseapp.controller.utils import warn_user
from mouseapp.model.main_models import MainModel
from mouseapp.model.settings.utils import Denoising, Detection
from mouseapp.view import utils
from mouseapp.view.generated.settings.ui_denoising_settings import (
    Ui_DenoisingSettingsWidget,)
from mouseapp.view.preview_settings_view import PreviewSettingsWindow
from mouseapp.view.widgets import SliderWithEdit


class DenoisingSettingsWindow(QtWidgets.QWidget, Ui_DenoisingSettingsWidget):
    """Denoising settings window class."""

    def __init__(self, model: MainModel):
        super(DenoisingSettingsWindow, self).__init__()
        self.setupUi(self)
        self.model = model

        # enforce garbage collection of this window
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.preview = PreviewSettingsWindow(self.model)
        self.verticalLayout.addWidget(self.preview)

        # connect inputs
        # # connect denoising inputs
        self.denoisingComboBox.currentTextChanged.connect(self.change_denoising_page)
        self.preview.previewButton.clicked.connect(self._on_preview_time)
        self.preview.runPreviewButton.hide()
        # bilateral
        self.sigmaSpaceLineEdit.editingFinished.connect(self._on_sigma_space_edit)
        self.sigmaColorLineEdit.editingFinished.connect(self._on_sigma_color_edit)
        self.dLineEdit.editingFinished.connect(self._on_d_edit)
        self.restoreBilateralButton.clicked.connect(self._on_bilateral_restore)
        # SDTS
        self.mLineEdit.editingFinished.connect(self._on_m_edit)
        self.SDTSNoiseDecreaseSlider = utils.initialize_widget(
            SliderWithEdit(minimum=0, maximum=1, resolution=100))
        self.SDTSLeftGridLayout.replaceWidget(self.placeholderSDTSNoiseDecreaseSlider,
                                              self.SDTSNoiseDecreaseSlider)
        self.placeholderSDTSNoiseDecreaseSlider.deleteLater()
        self.SDTSNoiseDecreaseSlider.modifications_finished.connect(
            self._on_sdts_noise_decrease_edit)
        self.restoreSDTSButton.clicked.connect(self._on_sdts_restore)
        # noise gate
        self.nGradFreqLineEdit.editingFinished.connect(self._on_n_grad_freq_edit)
        self.nGradTimeLineEdit.editingFinished.connect(self._on_n_grad_time_edit)
        self.nStdThreshLineEdit.editingFinished.connect(self._on_n_std_thresh_edit)
        self.noiseGateNoiseDecreaseSlider = utils.initialize_widget(
            SliderWithEdit(minimum=0, maximum=1, resolution=100))
        self.noiseGateLeftGridLayout.replaceWidget(
            self.placeholderNoiseGateNoiseDecreaseSlider,
            self.noiseGateNoiseDecreaseSlider,
        )
        self.placeholderNoiseGateNoiseDecreaseSlider.deleteLater()
        self.noiseGateNoiseDecreaseSlider.modifications_finished.connect(
            self._on_noise_gate_noise_decrease_edit)
        self.noiseStartLineEdit.editingFinished.connect(self._on_noise_start_end_edit)
        self.noiseEndLineEdit.editingFinished.connect(self._on_noise_start_end_edit)
        self.restoreNoiseGateButton.clicked.connect(self._on_noise_gate_restore)
        self.noiseAudioCheckBox.setCheckState(QtCore.Qt.Checked)
        self.loadNoiseAudioButton.setEnabled(False)
        self.noiseAudioCheckBox.stateChanged.connect(
            self._on_noise_audio_checkbox_changed)
        self.loadNoiseAudioButton.clicked.connect(self._on_load_noise_audio)

        # signals
        self.model.settings_model.denoising_spec_changed.connect(
            partial(self.preview.draw_upper_spect, y_label_prefix="~Before~"))
        self.model.settings_model.chosen_denoising_method_signal.connect(
            self.change_denoising_method)
        # no filter
        self.model.settings_model.no_filter_model.preview_model.preview_changed.connect(
            partial(self.preview.draw_lower_spect, y_label_prefix="~After~"))
        # bilateral
        self.model.settings_model.bilateral_model.preview_model.preview_changed.connect(
            partial(self.preview.draw_lower_spect, y_label_prefix="~After~"))
        self.model.settings_model.bilateral_model.sigma_color_changed.connect(
            self._on_sigma_color_signal)
        self.model.settings_model.bilateral_model.sigma_space_changed.connect(
            self._on_sigma_space_signal)
        self.model.settings_model.bilateral_model.d_changed.connect(self._on_d_signal)
        # SDTS
        self.model.settings_model.sdts_model.preview_model.preview_changed.connect(
            partial(self.preview.draw_lower_spect, y_label_prefix="~After~"))
        self.model.settings_model.sdts_model.m_changed.connect(self._on_m_signal)
        self.model.settings_model.sdts_model.noise_decrease_changed.connect(
            self._on_sdts_noise_decrease_signal)
        # noise gate
        self.model.settings_model.noise_gate_model.preview_model.preview_changed.connect(
            partial(self.preview.draw_lower_spect, y_label_prefix="~After~"))
        self.model.settings_model.noise_gate_model.n_grad_freq_changed.connect(
            self._on_n_grad_freq_signal)
        self.model.settings_model.noise_gate_model.n_grad_time_changed.connect(
            self._on_n_grad_time_signal)
        self.model.settings_model.noise_gate_model.n_std_thresh_changed.connect(
            self._on_n_std_thresh_signal)
        self.model.settings_model.noise_gate_model.noise_decrease_changed.connect(
            self._on_noise_gate_noise_decrease_signal)
        self.model.settings_model.noise_gate_model.noise_start_changed.connect(
            self._on_noise_start_signal)
        self.model.settings_model.noise_gate_model.noise_end_changed.connect(
            self._on_noise_end_signal)
        self.model.settings_model.noise_gate_model.noise_spectrogram_data_changed.connect(
            self._on_noise_spectrogram_data_signal)
        self.model.settings_model.noise_gate_model.use_main_spectrogram_changed.connect(
            self._on_use_main_spectrogram_signal)
        self.model.settings_model.noise_gate_model.noise_audio_changed.connect(
            self._on_noise_audio_signal)
        self.model.settings_model.noise_gate_model.passive_noise_audio_changed.connect(
            self._on_passive_noise_audio_signal)

        logging.debug("[DenoisingSettingsWindow] Finished initialization")

    def change_denoising_method(self, text: str):
        text_map = {
            Denoising.NO_FILTER: 0,
            Denoising.BILATERAL: 1,
            Denoising.SDTS: 2,
            Denoising.NOISE_GATE: 3,
        }
        self.denoisingComboBox.setCurrentIndex(text_map[text])
        self.change_denoising_page(text)

    def change_denoising_page(self, text: str):
        common_settings_controller.set_chosen_denoising_method(self.model, text.lower())
        if (self.model.settings_model.chosen_detection_method == Detection.NN and
                Denoising.NO_FILTER != text.lower()):
            warn_user(
                self.model,
                "Neural Network wasn't prepared for a denoised spectrogram! "
                "Quality of detected USVs may be low.",
            )
        if Denoising.NO_FILTER in text.lower():
            self.denoisingStackedWidget.setCurrentWidget(self.noFilterPage)
            no_filter_settings_controller.set_no_filter_preview(self.model)
        elif Denoising.BILATERAL in text.lower():
            self.denoisingStackedWidget.setCurrentWidget(self.bilateralPage)
            bilateral_settings_controller.emit_settings_signals(self.model)
            bilateral_settings_controller.set_bilateral_preview(self.model)
        elif Denoising.SDTS in text.lower():
            self.denoisingStackedWidget.setCurrentWidget(self.SDTSPage)
            sdts_settings_controller.emit_settings_signals(self.model)
            sdts_settings_controller.set_sdts_preview(self.model)
        elif Denoising.NOISE_GATE in text.lower():
            self.denoisingStackedWidget.setCurrentWidget(self.noiseGatePage)
            noise_gate_settings_controller.emit_settings_signals(self.model)
            noise_gate_settings_controller.set_noise_gate_preview(self.model)
        else:
            warnings.warn(f"Denoising method: {text.lower()} not supported")

    def _on_preview_time(self):
        common_settings_controller.set_preview_start_end(
            model=self.model,
            prev_start=self.preview.previewStartLineEdit.text(),
            prev_end=self.preview.previewEndLineEdit.text())
        if self.denoisingStackedWidget.currentWidget() == self.noFilterPage:
            no_filter_settings_controller.set_no_filter_preview(self.model)
        elif self.denoisingStackedWidget.currentWidget() == self.bilateralPage:
            bilateral_settings_controller.set_bilateral_preview(self.model)
        elif self.denoisingStackedWidget.currentWidget() == self.SDTSPage:
            sdts_settings_controller.set_sdts_preview(self.model)
        elif self.denoisingStackedWidget.currentWidget() == self.noiseGatePage:
            noise_gate_settings_controller.set_noise_gate_preview(self.model)
        else:
            warnings.warn("Current denoising page not supported")

    # bilateral

    def _on_bilateral_restore(self):
        bilateral_settings_controller.restore_default_bilateral_values(self.model)

    def _on_sigma_space_edit(self):
        bilateral_settings_controller.set_sigma_space(
            model=self.model, value=self.sigmaSpaceLineEdit.text())

    def _on_sigma_color_edit(self):
        bilateral_settings_controller.set_sigma_color(
            model=self.model, value=self.sigmaColorLineEdit.text())

    def _on_d_edit(self):
        bilateral_settings_controller.set_d(model=self.model,
                                            value=int(self.dLineEdit.text()))

    def _on_sigma_space_signal(self, value: float):
        bilateral_settings_controller.set_bilateral_preview(self.model)
        self.sigmaSpaceLineEdit.setText(str(value))

    def _on_sigma_color_signal(self, value: float):
        bilateral_settings_controller.set_bilateral_preview(self.model)
        self.sigmaColorLineEdit.setText(str(value))

    def _on_d_signal(self, value: int):
        bilateral_settings_controller.set_bilateral_preview(self.model)
        self.dLineEdit.setText(str(value))

    # SDTS

    def _on_sdts_restore(self):
        sdts_settings_controller.restore_default_sdts_values(self.model)

    def _on_m_edit(self):
        sdts_settings_controller.set_m(model=self.model,
                                       value=int(self.mLineEdit.text()))

    def _on_sdts_noise_decrease_edit(self, value: float):
        sdts_settings_controller.set_noise_decrease(model=self.model, value=value)

    def _on_m_signal(self, value: int):
        sdts_settings_controller.set_sdts_preview(self.model)
        self.mLineEdit.setText(str(value))

    def _on_sdts_noise_decrease_signal(self, value: float):
        sdts_settings_controller.set_sdts_preview(self.model)
        self.SDTSNoiseDecreaseSlider.set_value(value)

    # noise gate

    def _on_noise_gate_restore(self):
        noise_gate_settings_controller.restore_default_noise_gate_values(self.model)

    def _on_n_grad_freq_edit(self):
        noise_gate_settings_controller.set_n_grad_freq(
            model=self.model, value=int(self.nGradFreqLineEdit.text()))

    def _on_n_grad_time_edit(self):
        noise_gate_settings_controller.set_n_grad_time(
            model=self.model, value=int(self.nGradTimeLineEdit.text()))

    def _on_n_std_thresh_edit(self):
        noise_gate_settings_controller.set_n_std_thresh(
            model=self.model, value=self.nStdThreshLineEdit.text())

    def _on_noise_gate_noise_decrease_edit(self, value: float):
        noise_gate_settings_controller.set_noise_decrease(model=self.model, value=value)

    def _on_noise_start_end_edit(self):
        noise_gate_settings_controller.set_noise_start_end(
            model=self.model,
            noise_start=self.noiseStartLineEdit.text(),
            noise_end=self.noiseEndLineEdit.text())

    def _on_load_noise_audio(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self,
                                                     "Select audio files",
                                                     Path("").__str__(),
                                                     "Audio files (*.wav *.mp3)")[0]
        noise_gate_settings_controller.load_noise_audio(model=self.model,
                                                        file=Path(file))

    def _on_noise_audio_checkbox_changed(self):
        self.loadNoiseAudioButton.setEnabled(not self.noiseAudioCheckBox.isChecked())
        noise_gate_settings_controller.set_use_main_spectrogram(
            self.model, self.noiseAudioCheckBox.isChecked())

    def _on_use_main_spectrogram_signal(self, value: tuple):
        checked, file = value
        if checked:
            self.noiseAudioCheckBox.setCheckState(QtCore.Qt.Checked)
            self.loadNoiseAudioButton.setEnabled(False)
            self.noiseLabel.setText("")
        else:
            self.noiseAudioCheckBox.setCheckState(QtCore.Qt.Unchecked)
            self.loadNoiseAudioButton.setEnabled(True)
            if file is not None:
                self.noiseLabel.setText(f"Noise source: {file.name}")
        noise_gate_settings_controller.set_noise_gate_preview(self.model)

    def _on_noise_audio_signal(self, value):
        self.noiseLabel.setText(f"Noise source: {value.name}")
        noise_gate_settings_controller.load_noise_audio(self.model, value)

    def _on_passive_noise_audio_signal(self, value):
        self.noiseLabel.setText(f"Noise source: {value.name}")

    def _on_n_grad_freq_signal(self, value: int):
        noise_gate_settings_controller.set_noise_gate_preview(self.model)
        self.nGradFreqLineEdit.setText(str(value))

    def _on_n_grad_time_signal(self, value: int):
        noise_gate_settings_controller.set_noise_gate_preview(self.model)
        self.nGradTimeLineEdit.setText(str(value))

    def _on_n_std_thresh_signal(self, value: float):
        noise_gate_settings_controller.set_noise_gate_preview(self.model)
        self.nStdThreshLineEdit.setText(str(value))

    def _on_noise_gate_noise_decrease_signal(self, value: float):
        noise_gate_settings_controller.set_noise_gate_preview(self.model)
        self.noiseGateNoiseDecreaseSlider.set_value(value)

    def _on_noise_start_signal(self, value: int):
        noise_gate_settings_controller.set_noise_gate_preview(self.model)
        self.noiseStartLineEdit.setText(str(value))

    def _on_noise_end_signal(self, value: int):
        noise_gate_settings_controller.set_noise_gate_preview(self.model)
        self.noiseEndLineEdit.setText(str(value))

    def _on_noise_spectrogram_data_signal(self):
        noise_gate_settings_controller.set_noise_gate_preview(self.model)
