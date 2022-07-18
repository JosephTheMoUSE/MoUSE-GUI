"""Small custom widgets."""
import warnings
from collections.abc import Callable
from enum import Flag, auto
from numbers import Real
from typing import Optional

import numpy as np
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Signal
from matplotlib import pyplot as plt
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle

from mouseapp.controller import main_controller
from mouseapp.model.main_models import MainModel
from mouseapp.model.utils import Annotation
from mouseapp.view import utils
from mouseapp.view.generated.init_project.ui_project_entry import Ui_ProjectEntry
from mouseapp.view.generated.key_value_metadata.ui_key_value_widget import Ui_KeyValue
from mouseapp.view.generated.key_value_metadata.ui_new_key_value_widget import (
    Ui_NewKeyValue,)
from mouseapp.view.generated.ui_filename_widget import Ui_FileNameWidget
from mouseapp.view.generated.ui_progress_bar import Ui_ProgressBar


class NewKeyValue(QtWidgets.QWidget, Ui_NewKeyValue):

    def __init__(self, model):
        super(NewKeyValue, self).__init__()
        self.setupUi(self)

        # Makes the new key value window stay on top of the application
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.model = model

        # Connect actions
        self.addKeyValueButton.clicked.connect(
            lambda: main_controller.add_key_value_metadata(
                model=self.model,
                key_value=(
                    self.keyEditField.toPlainText(),
                    self.valueEditField.toPlainText(),
                ),
                value_type=self.valueTypeComboBox.currentText(),
            ))


class KeyValue(QtWidgets.QWidget, Ui_KeyValue):

    def __init__(self, model, key_value_type):
        super(KeyValue, self).__init__()
        self.setupUi(self)
        self.keyLabel.setText(key_value_type[0])
        self.valueEditField.setText(str(key_value_type[1]))
        self.valueTypeComboBox.setCurrentText(key_value_type[2])
        self.key = key_value_type[0]

        self.model = model
        self.key_value_type = key_value_type

        # Connect actions
        self.removeKeyValueButton.clicked.connect(
            lambda: main_controller.remove_key_value_metadata(model, key_value_type[0]))
        self.valueEditField.textChanged.connect(
            lambda: main_controller.update_key_value_metadata(
                model, key=key_value_type[0], value=self.valueEditField.toPlainText()))
        self.valueTypeComboBox.currentIndexChanged.connect(
            lambda: main_controller.update_key_value_metadata(
                model,
                key=key_value_type[0],
                vtype=self.valueTypeComboBox.currentText()))

        # Connect signals
        self.model.project_model.project_metadata_updated.connect(
            self.on_key_value_type_update)

    def on_key_value_type_update(self, key_value_type):
        if self.key == key_value_type[0]:
            cursor = self.valueEditField.textCursor()
            cursor_position = cursor.position()
            self.valueEditField.setText(str(key_value_type[1]))
            self.valueTypeComboBox.setCurrentText(key_value_type[2])
            # Make sure that cursor stays at the same position
            cursor.setPosition(cursor_position)
            self.valueEditField.setTextCursor(cursor)


class ProjectEntry(QtWidgets.QWidget, Ui_ProjectEntry):
    """Project Entry widget class."""

    def __init__(self, mouse_project):
        super(ProjectEntry, self).__init__()
        self.setupUi(self)

        self.projectNameLabel.setText(mouse_project.name)
        self.projectPathLabel.setText(str(mouse_project.path))
        self.projectNameLabel.setStyleSheet("font-weight: bold")
        self.projectPathLabel.setStyleSheet("color: gray")

        self.mouse_project = mouse_project


class Canvas(FigureCanvas):

    def __init__(self, *args, **kwargs):
        figure, axis = plt.subplots(*args, **kwargs)
        self.axis = axis
        # figure = Figure()  # TODO: resizing?
        super().__init__(figure)


class FileName(QtWidgets.QWidget, Ui_FileNameWidget):

    def __init__(self, model, file_name):
        super(FileName, self).__init__()
        self.setupUi(self)

        self.model = model
        self.file_name = file_name
        self.fileName.setText(file_name)

        # Connect buttons
        self.removeButton.clicked.connect(
            lambda: main_controller.remove_audio_file(self.model, self.file_name))

        # Hide the button as its currently unused
        self.removeButton.hide()


class TaskProgressbar(QtWidgets.QWidget, Ui_ProgressBar):

    def __init__(self, hide_stop_button: bool):
        super(TaskProgressbar, self).__init__()
        self.setupUi(self)
        self.buttonClicked = self.stopTaskToolButton.clicked
        if hide_stop_button:
            self.stopTaskToolButton.hide()

    def set_values(self,
                   left_txt: Optional[str],
                   progress: Optional[int],
                   right_txt: Optional[str]):
        if isinstance(left_txt, str):
            self.leftLabel.show()
            self.leftLabel.setText(left_txt)
        elif left_txt is None:
            self.leftLabel.hide()

        if isinstance(right_txt, str):
            self.rightLabel.show()
            self.rightLabel.setText(right_txt)
        elif right_txt is None:
            self.rightLabel.hide()

        if isinstance(progress, int):
            self.progressBar.show()
            self.progressBar.setValue(progress)
        elif progress is None:
            self.progressBar.hide()
        else:
            warnings.warn(
                f"`progressBar` is set with value of type `{type(progress)}`. "
                f"This is not guaranteed to work as expected. Use int instead.")
            self.progressBar.setValue(progress)


class SliderWithEdit(QtWidgets.QWidget):
    """A widget implementing advanced slider.

    This widget should be self-contained. It may contain fragments of controller
    and model if needed.
    """

    modifications_finished = Signal(float)

    def __init__(self, minimum: float, maximum: float, resolution: int = 100):
        super().__init__()

        self.minimum = minimum
        self.maximum = maximum
        self.span = maximum - minimum
        self.resolution = resolution

        self.edit = utils.initialize_widget(QtWidgets.QLineEdit())
        self.slider = utils.initialize_widget(
            QtWidgets.QSlider(orientation=QtCore.Qt.Orientation.Horizontal))
        self.slider.setMaximum(resolution)
        self.slider.setMinimum(0)
        self.slider.setSingleStep(1)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.slider, stretch=3)
        self.layout.addWidget(self.edit, stretch=1)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.slider.valueChanged.connect(self._on_slider)
        self.edit.editingFinished.connect(self._on_edit)

    def set_value(self, value: float):
        self.edit.setText(str(value))
        self.slider.setValue(int((value - self.minimum) / self.span * self.resolution))

    def _on_slider(self, value: int):
        self.modifications_finished.emit(value / self.resolution * self.span +
                                         self.minimum)

    def _on_edit(self):
        from mouseapp.controller.utils import float_convert

        value = self.edit.text()
        f_value = float_convert(value)
        self.modifications_finished.emit(np.clip(f_value, self.minimum, self.maximum))


class MovableAnnotationBox:
    """Class that encapsulates rectangle with coresponding annotation and allows rectangle(annotation) resizing. # noqa

    Attributes
    ----------
        rect : Rectangle
            rectangle (`annotation`'s visible representation) that can be modified.
        annotation : Annotation
            annotation that coresponds to `rect`
        threshold : Real
            maximal distance (in pixels) from `rect` side to enter edit mode
        on_annocation_changed : Callable
            callback called after each `rect` change (called while dragging or resize action)
        on_transition_finished : Callable
            callback called after dragging/resizing is finished (called from `on_release`)
    """

    lock = None  # only one Box can be resized or dragged at a time
    rect_near_cursor = None  # control cursor shape
    motion_type = None
    initial_event = None  # initial position of mouse click
    initial_rect_position = None  # initial position of rect
    selected_annotation = None  # selected annotation to be highlited

    class BoxSide(Flag):
        """Enum with possible cursor positions relative to `rect`."""

        OUT = auto()
        LEFT = auto()
        RIGHT = auto()
        BOTTOM = auto()
        TOP = auto()
        CENTER = auto()

    def __init__(
        self,
        rect: Rectangle,
        annotation: Annotation,
        model: MainModel,
        threshold: Real = 1,
        on_annotation_changed: Callable = None,
        on_transition_finished: Callable = None,
    ):
        self.rect = rect
        self.annotation = annotation
        self.threshold = threshold
        self.on_annotation_changed = on_annotation_changed
        self.on_transition_finished = on_transition_finished
        self.cid_press = None
        self.cid_release = None
        self.cid_drag = None
        self.model = model

    def connect(self):
        self.cid_press = self.rect.figure.canvas.mpl_connect("button_press_event",
                                                             self.on_press)
        self.cid_release = self.rect.figure.canvas.mpl_connect(
            "button_release_event", self.on_release)
        self.cid_drag = self.rect.figure.canvas.mpl_connect("motion_notify_event",
                                                            self.on_drag)

    def on_press(self, event):
        if self.lock is not None:
            return

        if event.button is MouseButton.RIGHT:
            contains, attributes = self._contains(event, threshold=self.threshold)
            if contains or attributes["on_side"]:
                main_controller.highlight_annotation(self.model, self.annotation)
        elif event.button is MouseButton.LEFT:
            contains, attributes = self._contains(event, threshold=self.threshold)
            if contains or attributes["on_side"]:
                MovableAnnotationBox.motion_type = attributes["side"]
                MovableAnnotationBox.lock = self
                MovableAnnotationBox.initial_event = event
                MovableAnnotationBox.initial_rect_position = self.rect.xy, (
                    self.rect.get_width(),
                    self.rect.get_height(),
                )

    def on_release(self, event):
        if MovableAnnotationBox.lock is not self:
            return
        MovableAnnotationBox.lock = None
        MovableAnnotationBox.initial_event = None
        MovableAnnotationBox.initial_rect_position = None
        if self.on_transition_finished is not None:
            (
                time_pixel_start,
                freq_pixel_start,
                time_pixel_end,
                freq_pixel_end,
            ) = utils.convert_rect_to_relative_pixels(self.rect)
            self.on_transition_finished(
                self.annotation,
                time_pixel_start,
                freq_pixel_start,
                time_pixel_end,
                freq_pixel_end,
            )

    def _get_box_position(self):
        x0, y0 = self.rect.get_xy()
        width, height = self.rect.get_width(), self.rect.get_height()
        x1, y1 = x0 + width, y0 + height
        # make sure we have bottom-left and top-right corner
        x0, x1 = sorted([x0, x1])
        y0, y1 = sorted([y0, y1])
        return x0, x1, y0, y1

    def on_drag(self, event):
        if self.lock is None:
            contains, attributes = self._contains(event)
            if contains:
                self.rect.figure.canvas.setCursor(QtCore.Qt.SizeAllCursor)
                MovableAnnotationBox.rect_near_cursor = self.rect
            elif attributes["on_side"] and attributes["side"] in [
                    MovableAnnotationBox.BoxSide.LEFT,
                    MovableAnnotationBox.BoxSide.RIGHT,
            ]:
                self.rect.figure.canvas.setCursor(QtCore.Qt.SizeHorCursor)
                MovableAnnotationBox.rect_near_cursor = self.rect
            elif attributes["on_side"] and attributes["side"] in [
                    MovableAnnotationBox.BoxSide.TOP,
                    MovableAnnotationBox.BoxSide.BOTTOM,
            ]:
                self.rect.figure.canvas.setCursor(QtCore.Qt.SizeVerCursor)
                MovableAnnotationBox.rect_near_cursor = self.rect
            elif self.rect is self.rect_near_cursor:  # we left this rect
                MovableAnnotationBox.rect_near_cursor = None
                self.rect.figure.canvas.setCursor(QtCore.Qt.ArrowCursor)
        else:
            if MovableAnnotationBox.lock is not self:
                return
            (x0, y0), (width0, height0) = self.initial_rect_position
            event_x, event_y = (
                np.rint(event.xdata).astype(int),
                np.rint(event.ydata).astype(int),
            )
            dx = event_x - np.rint(self.initial_event.xdata).astype(int)
            dy = event_y - np.rint(self.initial_event.ydata).astype(int)
            if MovableAnnotationBox.motion_type == self.BoxSide.CENTER:
                self.rect.set_x(x0 + dx)
                self.rect.set_y(y0 + dy)
            if MovableAnnotationBox.motion_type == self.BoxSide.LEFT:
                if width0 - dx >= 1:
                    self.rect.set_x(x0 + dx)
                    self.rect.set_width(width0 - dx)
            if MovableAnnotationBox.motion_type == self.BoxSide.TOP:
                if height0 + dy >= 1:
                    self.rect.set_height(height0 + dy)
            if MovableAnnotationBox.motion_type == self.BoxSide.RIGHT:
                if width0 + dx >= 1:
                    self.rect.set_width(width0 + dx)
            if MovableAnnotationBox.motion_type == self.BoxSide.BOTTOM:
                if height0 - dy >= 1:
                    self.rect.set_y(y0 + dy)
                    self.rect.set_height(height0 - dy)

            if self.on_annotation_changed is not None:
                (
                    time_pixel_start,
                    freq_pixel_start,
                    time_pixel_end,
                    freq_pixel_end,
                ) = utils.convert_rect_to_relative_pixels(self.rect)
                self.on_annotation_changed(
                    self.annotation,
                    time_pixel_start,
                    freq_pixel_start,
                    time_pixel_end,
                    freq_pixel_end,
                )
            self.rect.figure.canvas.draw_idle()

    def disconnect(self):
        self.rect.figure.canvas.mlp_disconnect(self.cid_press)
        self.rect.figure.canvas.mlp_disconnect(self.cid_release)
        self.rect.figure.canvas.mlp_disconnect(self.cid_drag)

    def _contains(self, event, threshold=1):
        contains, attributes = self.rect.contains(event)
        attributes["on_side"] = False
        attributes["side"] = MovableAnnotationBox.BoxSide.OUT
        if contains:
            attributes["side"] = MovableAnnotationBox.BoxSide.CENTER
            return contains, attributes
        else:
            x0, x1, y0, y1 = self._get_box_position()

            event_x, event_y = event.xdata, event.ydata
            if event_x is None or event_y is None:
                return contains, attributes

            if y0 <= event_y <= y1:
                if 0 < x0 - event_x < threshold:
                    attributes["on_side"] = True
                    attributes["side"] = MovableAnnotationBox.BoxSide.LEFT
                elif 0 < event_x - x1 < threshold:
                    attributes["on_side"] = True
                    attributes["side"] = MovableAnnotationBox.BoxSide.RIGHT

            if x0 <= event_x <= x1:
                if 0 < y0 - event_y < 2 * threshold:
                    attributes["on_side"] = True
                    attributes["side"] = MovableAnnotationBox.BoxSide.BOTTOM
                elif 0 < event_y - y1 < 2 * threshold:
                    attributes["on_side"] = True
                    attributes["side"] = MovableAnnotationBox.BoxSide.TOP
        return contains, attributes

    @staticmethod
    def select(mab):
        if MovableAnnotationBox.selected_annotation is not None:
            MovableAnnotationBox.selected_annotation.rect.set(edgecolor="red")

        MovableAnnotationBox.selected_annotation = mab
        mab.rect.set(edgecolor="green")
