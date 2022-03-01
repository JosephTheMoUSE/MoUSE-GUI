from typing import Union, Iterable

import numpy as np
from PySide6 import QtWidgets
from matplotlib.patches import Rectangle


def initialize_widget(widget: QtWidgets.QWidget):
    widget.show()
    widget.activateWindow()
    widget.raise_()
    return widget


def initialize_basic_layout(parent: QtWidgets.QWidget,
                            widgets: Union[QtWidgets.QWidget,
                                           Iterable[QtWidgets.QWidget]]):
    if isinstance(widgets, QtWidgets.QWidget):
        widgets = (widgets,)

    layout = QtWidgets.QVBoxLayout()
    for widget in widgets:
        layout.addWidget(widget)
    parent.setLayout(layout)
    return layout


def convert_rect_to_relative_pixels(rect: Rectangle):
    rect_x, rect_y = rect.get_xy()
    start_x, end_x = sorted([rect_x, rect_x + rect.get_width()])
    start_y, end_y = sorted([rect_y, rect_y + rect.get_height()])

    time_pixel_start = np.rint(start_x).astype(int)
    freq_pixel_start = np.rint(start_y).astype(int)
    time_pixel_end = np.rint(end_x).astype(int)
    freq_pixel_end = np.rint(end_y).astype(int)
    return time_pixel_start, freq_pixel_start, time_pixel_end, freq_pixel_end
