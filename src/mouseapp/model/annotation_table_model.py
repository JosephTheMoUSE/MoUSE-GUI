import numpy as np
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
import warnings

from mouseapp.model import constants
from mouseapp.model.utils import Annotation, SerializableModel


class AnnotationTableModel(QAbstractTableModel, SerializableModel):

    delete_button_show = Signal(bool)

    def __init__(self, spectrogram_model, parent=None):
        super(AnnotationTableModel, self).__init__(parent)
        self._spectrogram_model = spectrogram_model
        self._annotations = []
        self._annotations_column_names = [
            constants.COL_BEGIN_TIME,
            constants.COL_END_TIME,
            constants.COL_LOW_FREQ,
            constants.COL_HIGH_FREQ,
            constants.COL_USV_LABEL,
            constants.COL_DETECTION_METHOD,
        ]
        self._checked_annotations_counter = 0

    def copy_with_view(self, new_view):
        """
        Creates a copy of the object but with new view.
        """
        new_model = AnnotationTableModel(self._spectrogram_model, new_view)
        new_model.annotations = self.annotations
        new_model.annotations_column_names = self.annotations_column_names
        new_model.checked_annotations_counter = self.checked_annotations_counter
        return new_model

    def to_dict(self):
        """
        This class inherits from some complicated class,
        so we don't use .to_dict() from serializable model, as it
        would iterate over all method fields.
        """
        print("serializing annotation model")
        result = {
            "annotations": [
                annotation.to_dict() for annotation in self.annotations
            ],
            "annotations_column_names": self.annotations_column_names,
        }
        return result

    def from_dict(self, property_dict):
        self.annotations = [
            Annotation.from_dict(**annotation)
            for annotation in property_dict["annotations"]
        ]
        self.annotations_column_names = property_dict[
            "annotations_column_names"]

    def rowCount(self, parent=None):
        return len(self.annotations)

    def columnCount(self, parent=None):
        return len(self.annotations_column_names)

    def data(self, index, role=Qt.DisplayRole):
        """Depending on the index and role given, return data. If not
        returning data, return None (PySide equivalent of QT's
        "invalid QVariant").
        """
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self._annotations):
            return None

        if role == Qt.DisplayRole:
            c = index.column()
            if c <= 3:
                return str(self.annotations[index.row()].table_data[
                    self.annotations_column_names[c]])
            elif c < len(self.annotations_column_names):
                return self.annotations[index.row()].table_data[
                    self.annotations_column_names[c]]

        return None

    def setData(self, index, value, role):
        column = self.annotations_column_names[index.column()]
        if role == Qt.EditRole:
            annotation = self.annotations[index.row()]
            if column in [
                    constants.COL_BEGIN_TIME,
                    constants.COL_END_TIME,
                    constants.COL_LOW_FREQ,
                    constants.COL_HIGH_FREQ,
            ]:
                try:
                    value = np.float64(value)
                except ValueError:
                    warnings.warn("Changed value should be a real number.")
                    return False

            if column == constants.COL_BEGIN_TIME:
                if value < annotation.time_end:
                    annotation.time_start = value
                    self._spectrogram_model.signal_visible_annotations()
                else:
                    warnings.warn(
                        "Begin Time (s) should be smaller than End Time (s)")
            elif column == constants.COL_END_TIME:
                if value > annotation.time_start:
                    annotation.time_end = value
                    self._spectrogram_model.signal_visible_annotations()
                else:
                    warnings.warn(
                        "Begin Time (s) should be smaller than End Time (s)")
            elif column == constants.COL_HIGH_FREQ:
                if value > annotation.freq_start:
                    annotation.freq_end = value
                    self._spectrogram_model.signal_visible_annotations()
                else:
                    warnings.warn(
                        "Low Freq (Hz) should be smaller than High Freq (Hz)")
            elif column == constants.COL_LOW_FREQ:
                if value < annotation.freq_end:
                    annotation.freq_start = value
                    self._spectrogram_model.signal_visible_annotations()
                else:
                    warnings.warn(
                        "Low Freq (Hz) should be smaller than High Freq (Hz)")
            elif column not in [constants.COL_DETECTION_METHOD]:
                annotation.table_data[column] = value

            return True
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Set the headers to be displayed."""
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal and section < len(
                self.annotations_column_names):
            return self.annotations_column_names[section]

        return None

    def removeRows(self, position, rows=1, index=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        del self.annotations[position:position + rows]
        self.endRemoveRows()
        return True

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    @property
    def annotations(self):
        return self._annotations

    @annotations.setter
    def annotations(self, annotations):
        if len(self._annotations) > 0:
            self.beginRemoveRows(QModelIndex(), 0, len(self.annotations) - 1)
            del self._annotations[:]
            self.endRemoveRows()

        self.append_annotations(annotations)

    def append_annotations(self, data):
        """Append rows into the model."""
        self.beginInsertRows(
            QModelIndex(),
            len(self._annotations),
            len(self._annotations) + len(data) - 1,
        )
        self._annotations += data
        self.endInsertRows()
        return True

    def update_all_displayed_data(self):
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.columnCount() - 1))

    @property
    def annotations_column_names(self):
        return self._annotations_column_names

    @annotations_column_names.setter
    def annotations_column_names(self, annotations_column_names):
        self._annotations_column_names = annotations_column_names

    def update_annotations_column_names(self, new_columns):
        for col_name in new_columns:
            if col_name not in self.annotations_column_names:
                self.annotations_column_names.append(col_name)

    @property
    def checked_annotations_counter(self):
        return self._checked_annotations_counter

    @checked_annotations_counter.setter
    def checked_annotations_counter(self, value):
        if self.checked_annotations_counter == 0 and value > 0:
            self.delete_button_show.emit(True)
        elif self.checked_annotations_counter > 0 and value == 0:
            self.delete_button_show.emit(False)
        self._checked_annotations_counter = value
