"""Main Window of the application."""
import copy
import os
from pathlib import Path
from sys import platform
from typing import List, Optional, Tuple

from PySide6 import QtGui
from PySide6 import QtWidgets
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication

import mouseapp.controller.classification_controller
from mouseapp.model import constants
from mouseapp.view.widgets import TaskProgressbar

os.environ["QT_API"] = "pyside6"
if platform == "darwin":
    os.environ["KMP_DUPLICATE_LIB_OK"] = "True"  # macOS bugfix

import numpy as np
from PySide6 import QtCore
from matplotlib.patches import Rectangle
from matplotlib.backend_bases import MouseButton

from mouseapp.view.settings_view import SettingsWindow
from mouseapp.controller import (  # yapf: disable
    persistency_controller,
    main_controller,
    detection_controller,  # yapf: disable
)
from mouseapp import context_manager
from mouseapp.model.main_models import MainModel
from mouseapp.model.annotation_table_model import AnnotationTableModel
from mouseapp.view import utils
from mouseapp.view import widgets
from mouseapp.view.generated.ui_mouse_main_window import Ui_MainWindow
from mouseapp.view.generated.ui_project_tab import Ui_ProjectWindow
from mouseapp.view.generated.ui_spectrogram_tab import Ui_SpectrogramWindow
from mouseapp.view.utils import initialize_widget
from mouse.utils import sound_util, visualization


class SpectrogramTab(QtWidgets.QWidget, Ui_SpectrogramWindow):
    """Spectrogram Tab class."""

    def __init__(self, model: MainModel):
        super(SpectrogramTab, self).__init__()
        self.setupUi(self)
        self.model = model
        self.signal_data = None
        self.spec_data = None
        self.spectrogram_displayed = False
        self.spectrogram_color_mesh = None
        self.time_mask_size = 0
        self.is_drawing = False
        self.current_annotation: Optional[Rectangle] = None
        self.time_ticks_mask = None
        self._annotation_boxes: List[widgets.MovableAnnotationBox] = []
        self.table_index: int = 0

        # Change squeakTable model to custom one
        old_model = self.squeakTable.model()
        if old_model is not None:
            self.table.setModel(None)
            old_model.deleteLater()

        new_model = main_controller.update_annotation_table_model(
            self.model, self.squeakTable)
        self.squeakTable.setModel(new_model)

        # Connect inputs
        self.spectrogramScrollBar.setSingleStep(
            self.model.spectrogram_model._slider_step_size)
        self.spectrogramScrollBar.setPageStep(
            self.model.spectrogram_model._slider_step_size * 10)
        self.detectButton.clicked.connect(
            lambda: detection_controller.process_spectrogram(self.model))
        self.classifyButton.clicked.connect(
            lambda: mouseapp.controller.classification_controller.
            run_selected_classification(self.model))
        self.deleteButton.setEnabled(False)
        self.deleteButton.clicked.connect(
            lambda: main_controller.delete_selected_annotations(self.model))
        self.deleteAllButton.clicked.connect(self._on_delete_all_clicked)
        self.filterButton.clicked.connect(
            lambda: main_controller.filter_annotations(self.model))

        # Connect signals
        self.spectrogramScrollBar.valueChanged.connect(
            lambda position: main_controller.update_from_slider_position(
                self.model, position))
        self.model.project_model.audio_files_signal.connect(
            lambda audio_files: main_controller.update_signal_data(
                self.model, audio_files))
        # self.model.spectrogram_model.annotations_info_signal.connect(
        #     lambda column_names_and_annotations: self._show_annotations_info(
        #         column_names_and_annotations))
        self.model.spectrogram_model.slider_step_size_changed.connect(
            self._update_slider_params)
        self.model.spectrogram_model.spectrogram_data_changed.connect(self._reset_view)
        self.model.spectrogram_model.spectrogram_chunk_data_changed.connect(
            self._draw_spectrogram)
        self.model.spectrogram_model.visible_annotations_changed.connect(
            self._update_visible_annotations)
        # self.model.spectrogram_model.annotation_field_changed.connect(
        #     self._handle_annotation_field_changed)
        self.model.spectrogram_model.select_annotations.connect(
            self._handle_select_annotations)
        self.model.spectrogram_model.detection_allowed_changed.connect(
            self.detectButton.setEnabled)
        self.model.spectrogram_model.annotation_table_model.delete_button_show.connect(
            self._handle_delete_button_show)
        self.squeakTable.verticalHeader().sectionClicked.connect(
            self._show_annotation_on_spec)

        # Handle canvas
        self.canvas = widgets.Canvas()
        self.spectrogram_axis = self.canvas.figure.gca()
        self.spectrogramWidget.addWidget(self.canvas)
        self.canvas.figure.canvas.mpl_connect("button_press_event",
                                              self._on_button_pressed_event)
        self.canvas.figure.canvas.mpl_connect("button_release_event",
                                              self._on_button_released_event)
        self.canvas.figure.canvas.mpl_connect("motion_notify_event",
                                              self._on_mouse_motion)

        # Hide unused widgets
        self.windowSizeLabel.hide()
        self.winowSizeSlider.hide()
        self.nfftLabel.hide()
        self.nfttSlider.hide()
        self.overlapLabel.hide()
        self.overlapSlider.hide()

    def _on_button_pressed_event(self, event):
        if event.button is not MouseButton.LEFT:
            return

        if widgets.MovableAnnotationBox.rect_near_cursor is not None:
            for mab in self._annotation_boxes:
                mab.on_press(event)
            return

        self.current_annotation = Rectangle(
            (np.rint(event.xdata).astype(int), np.rint(event.ydata).astype(int)),
            0,
            0,
            linewidth=1,
            edgecolor="r",
            facecolor="none",
        )
        self.is_drawing = True
        self.spectrogram_axis.add_patch(self.current_annotation)
        self.canvas.draw_idle()

    def _on_button_released_event(self, event):
        if event.button is not MouseButton.LEFT:
            return

        if widgets.MovableAnnotationBox.lock is not None:
            widgets.MovableAnnotationBox.lock.on_release(event)
            return

        cursor_x = event.xdata
        cursor_y = event.ydata
        if self.is_drawing:
            annotation_x, annotation_y = self.current_annotation.get_xy()
            if cursor_x is not None:
                self.current_annotation.set_width(cursor_x - annotation_x)
            if cursor_y is not None:
                self.current_annotation.set_height(cursor_y - annotation_y)

            (
                time_pixel_start,
                freq_pixel_start,
                time_pixel_end,
                freq_pixel_end,
            ) = utils.convert_rect_to_relative_pixels(self.current_annotation)

            self.current_annotation.remove()
            self.current_annotation = None
            self.is_drawing = False

            if (time_pixel_end - time_pixel_start != 0 and
                    freq_pixel_end - freq_pixel_start):
                main_controller.add_new_annotation(
                    self.model,
                    time_pixel_start=time_pixel_start,
                    freq_pixel_start=freq_pixel_start,
                    time_pixel_end=time_pixel_end,
                    freq_pixel_end=freq_pixel_end,
                )
            else:
                self.canvas.draw_idle()

    def _on_mouse_motion(self, event):
        cursor_x = event.xdata
        cursor_y = event.ydata

        if self.is_drawing:
            annotation_x, annotation_y = self.current_annotation.get_xy()
            if cursor_x is not None:
                self.current_annotation.set_width(cursor_x - annotation_x)
            if cursor_y is not None:
                self.current_annotation.set_height(cursor_y - annotation_y)
            self.canvas.draw_idle()
        else:
            for mab in self._annotation_boxes:
                mab.on_drag(event)

    def _update_slider_params(self, step_size):
        self.spectrogramScrollBar.setSingleStep(step_size)
        self.spectrogramScrollBar.setPageStep(step_size * 10)

    def _reset_view(self, spectrogram_data_and_size):
        spectrogram_data, display_size = spectrogram_data_and_size
        self.spectrogram_displayed = False
        if spectrogram_data is not None:
            self.spectrogramScrollBar.setMaximum(spectrogram_data.times[-1] * 1000 -
                                                 display_size)
            self.spectrogramScrollBar.setSliderPosition(0)
            self.spectrogramScrollBar.setValue(0)
            main_controller.update_from_slider_position(
                self.model, 0)  # TODO: why this is not called
        else:
            self.spectrogramScrollBar.setMaximum(0)
            self.canvas.figure.clf()
            self.canvas.draw_idle()

    def remove_annotations(self):
        annotations = list(self.spectrogram_axis.patches)
        for annotation in annotations:
            annotation.remove()

    def _update_visible_annotations(self, annotation_data):
        visible_annotations, times, display_start_time, freqs = annotation_data
        self.remove_annotations()
        self._annotation_boxes: List[widgets.MovableAnnotationBox] = []
        # allow garbage collection of mabs that may
        # be referenced by static variables
        widgets.MovableAnnotationBox.lock = None
        widgets.MovableAnnotationBox.selected_annotation = None

        def find_nearest(t, arr):
            return np.abs(arr - t).argmin()

        # cast annotation positions to relative spectrogram coordinates
        x_start = find_nearest(display_start_time, times)
        for annotation in visible_annotations:
            # todo(werekaaa): How to do it efficiently?
            annotation_start_time = find_nearest(annotation.time_start, times)
            annotation_end_time = find_nearest(annotation.time_end, times)
            annotation_start_freq = find_nearest(annotation.freq_start, freqs)
            annotation_end_freq = find_nearest(annotation.freq_end, freqs)

            x = annotation_start_time - x_start
            y = annotation_start_freq
            width = annotation_end_time - annotation_start_time
            height = annotation_end_freq - annotation_start_freq

            rect = Rectangle((x, y),
                             width,
                             height,
                             linewidth=1,
                             edgecolor="r",
                             facecolor="none")
            self.spectrogram_axis.add_patch(rect)
            mab = widgets.MovableAnnotationBox(
                rect,
                annotation,
                on_transition_finished=lambda *x: main_controller.update_annotation(
                    self.model, *x),
            )

            self._annotation_boxes.append(mab)
        self.canvas.draw_idle()

    # def _show_annotations_info(self, column_names_and_annotations):
    #     column_names, annotations = copy.deepcopy(column_names_and_annotations)
    #     self.squeakTable.setRowCount(len(annotations))
    #     self.squeakTable.setColumnCount(len(column_names))
    #     column_names[0] = '      | ' + column_names[0]
    #     self.squeakTable.setHorizontalHeaderLabels(column_names)
    #
    #     header = self.squeakTable.horizontalHeader()
    #     for i in range(len(column_names)):
    #         header.setSectionResizeMode(i,
    #                                     QtWidgets.QHeaderView.ResizeToContents)
    #     self.squeakTable.setSortingEnabled(False)
    #     for i, annotation in enumerate(annotations):
    #         QApplication.processEvents()  # prevents freezing of the application
    #
    #         item = self.squeakTable.item(i, 0)
    #         if item is None:
    #             time_start_item = QtWidgets.QTableWidgetItem(
    #                 f"{annotation.time_start}")
    #             if annotation.checked:
    #                 time_start_item.setCheckState(QtCore.Qt.CheckState.Checked)
    #             else:
    #                 time_start_item.setCheckState(
    #                     QtCore.Qt.CheckState.Unchecked)
    #             self.squeakTable.setItem(i, 0, time_start_item)
    #         else:
    #             if annotation.checked:
    #                 item.setCheckState(QtCore.Qt.CheckState.Checked)
    #             else:
    #                 item.setCheckState(QtCore.Qt.CheckState.Unchecked)
    #
    #         item = self.squeakTable.item(i, 1)
    #         if item is None:
    #             time_end_item = QtWidgets.QTableWidgetItem(
    #                 f"{annotation.time_end}")
    #             self.squeakTable.setItem(i, 1, time_end_item)
    #         else:
    #             item.setText(f"{annotation.time_end}")
    #
    #         item = self.squeakTable.item(i, 2)
    #         if item is None:
    #             freq_start_item = QtWidgets.QTableWidgetItem(
    #                 f"{annotation.freq_start}")
    #             self.squeakTable.setItem(i, 2, freq_start_item)
    #         else:
    #             item.setText(f"{annotation.freq_start}")
    #
    #         item = self.squeakTable.item(i, 3)
    #         if item is None:
    #             freq_end_item = QtWidgets.QTableWidgetItem(
    #                 f"{annotation.freq_end}")
    #             self.squeakTable.setItem(i, 3, freq_end_item)
    #         else:
    #             item.setText(f"{annotation.freq_end}")
    #
    #         item = self.squeakTable.item(i, 4)
    #         if item is None:
    #             label_item = QtWidgets.QTableWidgetItem(f"{annotation.label}")
    #             self.squeakTable.setItem(i, 4, label_item)
    #         else:
    #             item.setText(f"{annotation.label}")
    #
    #         for j in range(5, len(column_names)):
    #             item = self.squeakTable.item(i, j)
    #             if item is None:
    #                 table_data_item = QtWidgets.QTableWidgetItem(
    #                     f"{annotation.table_data[column_names[j]]}")
    #                 self.squeakTable.setItem(i, j, table_data_item)
    #             else:
    #                 item.setText(f"{annotation.table_data[column_names[j]]}")
    #
    #     self.squeakTable.itemChanged.connect(self._annotation_info_changed)

    def _on_delete_all_clicked(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText("Are you sure you want to delete all annotations?")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Cancel |
                                  QtWidgets.QMessageBox.Ok)
        ret = msgBox.exec_()

        if ret == QtWidgets.QMessageBox.Ok:
            main_controller.delete_all_annotations(self.model)

    def _handle_delete_button_show(self, state):
        if state:
            self.deleteButton.setEnabled(True)
        else:
            self.deleteButton.setEnabled(False)

    # todo(werkaaa): is this function necessary?
    # def _annotation_info_changed(self, item):
    #     idx = self.squeakTable.indexFromItem(item)
    #     main_controller.change_annotation_data(self.model,
    #                                            idx.row(),
    #                                            idx.column(),
    #                                            item)

    # def _handle_annotation_field_changed(self, data):
    #     self.squeakTable.item(data[0], data[1]).setText(f"{data[2]}")

    def _delete_all_annotations(self, row_ids):
        for i in row_ids[:-1]:
            self.squeakTable.removeRow(i)

    def _draw_spectrogram(self, spectrogram_data: sound_util.SpectrogramData):
        if not self.spectrogram_displayed:
            self.spectrogram_color_mesh = visualization.draw_spectrogram(
                spectrogram_data, ax=self.spectrogram_axis, vmax=5)

            self.spectrogram_displayed = True
        else:
            visualization.draw_spectrogram(
                spectrogram_data,
                ax=self.spectrogram_axis,
                colormesh=self.spectrogram_color_mesh,
                vmax=5,
            )

        self.canvas.draw_idle()

    def _show_annotation_on_spec(self, index: int):
        annotation_count = len(
            self.model.spectrogram_model.annotation_table_model.annotations)
        if annotation_count == 0:
            return

        self.table_index = np.clip(index, 0, annotation_count - 1)

        annotation = self.model.spectrogram_model.annotation_table_model.annotations[
            self.table_index]
        t_0 = annotation.table_data[constants.COL_BEGIN_TIME]
        position = 1000 * t_0 - self.model.spectrogram_model.annotation_margin
        position = max(0, position)
        position = min(position, self.spectrogramScrollBar.maximum())

        self.squeakTable.selectRow(self.table_index)
        self.spectrogramScrollBar.setSliderPosition(position)

        main_controller.update_from_slider_position(self.model, position)
        for mab in self._annotation_boxes:
            if mab.annotation == annotation:
                widgets.MovableAnnotationBox.select(mab)

    def _handle_select_annotations(self, selected: List):
        for id in selected:
            item = self.squeakTable.item(id, 0)
            item.setCheckState(QtCore.Qt.CheckState.Checked)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        super().keyReleaseEvent(event)

        if event.key() == QtCore.Qt.Key_Right:
            event.accept()
            self._show_annotation_on_spec(index=self.table_index + 1)
        if event.key() == QtCore.Qt.Key_Left:
            event.accept()
            self._show_annotation_on_spec(index=self.table_index - 1)
        event.ignore()


class ProjectTab(QtWidgets.QWidget, Ui_ProjectWindow):
    """Project Tab class."""

    def __init__(self, model: MainModel):
        super(ProjectTab, self).__init__()
        self.setupUi(self)

        self.model = model
        self.active_new_key_value_widget = None

        # Prepare dict for key_value widgets
        self.key_value_widgets = dict()
        self.audio_file_widgets = dict()

        # Connect actions
        self.addMetadataButton.clicked.connect(self._on_add_project_metadata)
        self.projectNameEdit.textChanged.connect(
            lambda: main_controller.set_project_name(model=model,
                                                     name=self.projectNameEdit.text()))
        self.dateEdit.dateChanged.connect(lambda: main_controller.set_experiment_date(
            model=model, date=self.dateEdit.date()))
        self.noteEdit.textChanged.connect(lambda: main_controller.set_project_note(
            model=model, note=self.noteEdit.toPlainText()))

        # Connect signals
        self.model.project_model.project_metadata_added.connect(
            self._on_project_metadata_added)
        self.model.project_model.project_metadata_removed.connect(
            self._on_project_metadata_removed)
        self.model.project_model.project_name_signal.connect(
            lambda project_name: self.projectNameEdit.setText(project_name))
        self.model.project_model.experiment_note_signal.connect(
            lambda experiment_note: self.noteEdit.setText(experiment_note))
        self.model.project_model.audio_files_signal.connect(
            lambda audio_files: self._on_audio_file_loaded(
                self._get_shortest_unique_names(audio_files)))
        self.model.project_model.experiment_date_signal.connect(
            lambda experiment_date: self.dateEdit.setDate(experiment_date))
        self.model.project_model.project_metadata_signal.connect(
            self._on_project_metadata_signal)

    @staticmethod
    def _get_shortest_unique_names(audio_files):
        if len(audio_files) > 0:
            audio_files_parts = [file.parts for file in audio_files]
        else:
            return []
        first_file = audio_files_parts[0]
        min_length = min([len(file) for file in audio_files_parts])
        last_common = min_length
        for i in range(min_length):
            for j in range(len(audio_files_parts)):
                if first_file[i] != audio_files_parts[j][i]:
                    last_common = i
                    break
            if last_common < min_length:
                break
        character_id = (sum([len(part) for part in first_file[:last_common]]) +
                        last_common - 1)
        character_id = min(character_id,
                           len(str(audio_files[0])) - len(audio_files[0].name))
        return [str(file_name)[character_id:] for file_name in audio_files]

    def _on_add_project_metadata(self):
        if not self.active_new_key_value_widget:
            self.active_new_key_value_widget = utils.initialize_widget(
                widgets.NewKeyValue(self.model))

            def remove_active_new_key_widget(_):
                self.active_new_key_value_widget = None

            self.active_new_key_value_widget.closeEvent = remove_active_new_key_widget

    def _on_project_metadata_added(self, key_value_type):
        # Close key_value_window
        if self.active_new_key_value_widget is not None:
            self.active_new_key_value_widget.hide()
            self.active_new_key_value_widget = None

        # If key already exists, raise exception
        # This issue should be handled in controller - user should be informed
        if key_value_type[0] in self.key_value_widgets:
            raise ValueError("Metadata key cannot be repeated.")

        # Create and add a new key_value_widget to the list
        key_value_widget = utils.initialize_widget(
            widgets.KeyValue(self.model, key_value_type))
        list_widget_item = QtWidgets.QListWidgetItem(self.keyValueList)
        list_widget_item.setSizeHint(key_value_widget.sizeHint())
        self.keyValueList.addItem(list_widget_item)
        self.keyValueList.setItemWidget(list_widget_item, key_value_widget)

        # Store key_value_widget so it can be removed if necessary
        self.key_value_widgets[key_value_type[0]] = key_value_widget

    def _on_project_metadata_removed(self, project_metadata):
        slider_position = self.keyValueList.verticalScrollBar().sliderPosition()
        self.keyValueList.clear()
        self.key_value_widgets.clear()
        self._on_project_metadata_signal(project_metadata)
        self.keyValueList.verticalScrollBar().setSliderPosition(slider_position)

    def _on_project_metadata_signal(self, project_metadata):
        for (key, value) in project_metadata.items():
            self._on_project_metadata_added((key, value[0], value[1]))

    def _on_audio_file_loaded(self, audio_files):
        slider_position = self.fileList.verticalScrollBar().sliderPosition()
        self.fileList.clear()
        self.audio_file_widgets.clear()
        for file_name in audio_files:
            item = utils.initialize_widget(widgets.FileName(self.model, file_name))
            list_widget_item = QtWidgets.QListWidgetItem(self.fileList)
            list_widget_item.setSizeHint(item.sizeHint())
            self.audio_file_widgets[file_name] = list_widget_item
            self.fileList.addItem(list_widget_item)
            self.fileList.setItemWidget(list_widget_item, item)
        self.fileList.verticalScrollBar().setSliderPosition(slider_position)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    """Main Window class."""

    def __init__(self, model: MainModel):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.show()

        self.model = model
        self.model.application_model.active_windows.add(self)
        self.save_label: Optional[QtWidgets.QLabel] = None
        self.progressbar: Optional[TaskProgressbar] = None
        self.settings_window = None  # for avoiding garbage collection

        # Instantiate spectrogram tab
        spectrogram_window = utils.initialize_widget(SpectrogramTab(model))
        utils.initialize_basic_layout(self.spectrogramTab, spectrogram_window)

        # Instantiate project tab
        project_window = utils.initialize_widget(ProjectTab(model))
        utils.initialize_basic_layout(self.projectTab, project_window)

        # Connect actions
        self.actionNewProject.triggered.connect(self._action_new_project)
        self.actionSave.triggered.connect(self._action_save)
        self.actionSaveAs.triggered.connect(self._action_save_as)
        self.actionLoadProject.triggered.connect(self._action_load_project)
        self.actionSettings.triggered.connect(self._action_settings)
        self.actionLoadAnnotations.triggered.connect(self._action_load_annotations)
        self.actionExport.triggered.connect(self._action_export_annotations)
        # todo (#75): remove unnecessary menu dropdown

        # Connect signals
        self.model.application_model.text_warning_signal.connect(
            self._on_text_warning_signal)
        self.model.spectrogram_model.progressbar_changed.connect(
            self._on_progressbar_definition)
        self.model.spectrogram_model.detection_info_changed.connect(
            self._on_progressbar_update)

        # Hide unused actions:
        self.actionSaveAs.setVisible(False)  # todo (#56)

    def _action_settings(self):
        self.settings_window = initialize_widget(SettingsWindow(self.model))

    def _action_new_project(self):
        context_manager.instantiate_project_creation_window(old_widget=self,
                                                            old_model=self.model)

    def _action_load_annotations(self):
        file = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select a file with annotations",
            Path("").__str__(),
            "Audio files (*.txt *.csv)",
        )[0]
        main_controller.load_annotations(model=self.model, filename=Path(file))

    def _action_load_project(self):
        context_manager.instantiate_project_load_window(old_widget=self,
                                                        old_model=self.model)

    def _action_export_annotations(self):
        filename = QtWidgets.QFileDialog().getSaveFileName(self, "Save File")[0]
        if filename != "":
            main_controller.export_annotations(self.model, Path(filename))

    def _action_save(self):
        """Save project and show message on statusbar."""
        # Clear previous message
        if self.save_label is not None:
            self.statusbar.removeWidget(self.save_label)

        result = persistency_controller.save_project(self.model)

        # Prepare and show save-status message
        self.save_label = initialize_widget(QtWidgets.QLabel())
        self.save_label.setText(result)
        self.statusbar.addWidget(self.save_label)

        # Remove save-status message after some time
        def _remove_label():
            self.statusbar.removeWidget(self.save_label)
            self.save_label = None

        QtCore.QTimer.singleShot(60000, _remove_label)

    def _action_save_as(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select audio files",
            Path(self.model.application_model.app_data_dir).__str__(),
            QtWidgets.QFileDialog.ShowDirsOnly |
            QtWidgets.QFileDialog.DontResolveSymlinks,
        )
        persistency_controller.save_project_as(folder=Path(folder), model=self.model)

    @Slot()
    def _on_progressbar_definition(self, defined: bool):
        if not defined:
            self.statusbar.removeWidget(self.progressbar)
            return

        if self.model.spectrogram_model.background_task is None:
            raise ValueError("Progress bar is associated with "
                             "`background_task`, but `background_task` is "
                             "`None`.")
        killable = self.model.spectrogram_model.background_task.is_killable()
        self.progressbar: TaskProgressbar = utils.initialize_widget(
            TaskProgressbar(hide_stop_button=not killable))
        if killable:
            self.progressbar.buttonClicked.connect(
                self.model.spectrogram_model.background_task.kill)
        self.statusbar.addWidget(self.progressbar)

    @Slot()
    def _on_progressbar_update(self,
                               value: Tuple[Optional[str], Optional[int],
                                            Optional[str]]):
        if isinstance(self.progressbar, TaskProgressbar):
            self.progressbar.set_values(left_txt=value[0],
                                        progress=value[1],
                                        right_txt=value[2])

    @staticmethod
    @Slot()
    def _on_text_warning_signal(warning):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(warning)
        msgBox.exec_()

    def closeEvent(self, event):
        if self in self.model.application_model.active_windows:
            self.model.application_model.active_windows.remove(self)
        persistency_controller.save_project(model=self.model)
        event.accept()
