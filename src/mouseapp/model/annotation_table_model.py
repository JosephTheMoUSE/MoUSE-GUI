from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QObject, Signal
from typing import Optional, Union, List
import warnings

from mouseapp.controller import utils
from mouseapp.model import constants
from mouseapp.model.utils import Annotation, SerializableModel


class AnnotationTableModel(QAbstractTableModel, SerializableModel):

    delete_button_show = Signal(bool)
    highlight_row = Signal(int)

    def __init__(self, spectrogram_model, parent: QObject = None):
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
        self.check_states = dict()

    def copy_with_view(self, new_view):
        """Create a copy of the object on which called but with new view."""
        new_model = AnnotationTableModel(self._spectrogram_model, new_view)
        new_model.annotations = self.annotations
        new_model.annotations_column_names = self.annotations_column_names
        new_model.checked_annotations_counter = self.checked_annotations_counter
        return new_model

    def to_dict(self):
        """Serialize in a custom way.

        This class inherits from some complicated class,
        so we don't use .to_dict() from serializable model, as it
        would iterate over all method fields.
        """
        result = {
            "annotations": [annotation.to_dict() for annotation in self.annotations],
            "annotations_column_names": self.annotations_column_names,
        }
        return result

    def from_dict(self, property_dict):
        self.annotations = [
            Annotation.from_dict(**annotation)
            for annotation in property_dict["annotations"]
        ]
        self.annotations_column_names = property_dict["annotations_column_names"]

    def rowCount(self, parent=None):
        """Used internally by Qt."""  # noqa
        return len(self.annotations)

    def columnCount(self, parent=None):
        """Used internally by Qt."""  # noqa
        return len(self.annotations_column_names)

    def data(self,
             index: QModelIndex,
             role=Qt.DisplayRole) -> Optional[Union[str, Qt.CheckState]]:
        """Depending on the index and role given, return data.

        This method is responsible for proper display in the view and is used
        internally by Qt.
        """
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self._annotations):
            return None

        if role == Qt.DisplayRole or role == Qt.EditRole:
            c = index.column()
            if c < len(self.annotations_column_names):
                return str(self.annotations[index.row()].table_data[
                    self.annotations_column_names[c]])
        if role == Qt.CheckStateRole and index.column() == 0:
            if self.annotations[index.row()].checked:
                return Qt.CheckState.Checked
            else:
                return Qt.CheckState.Unchecked

        return None

    def setData(self, index: QModelIndex, value: Union[str, Qt.CheckState], role: int):
        """Edit table data from GUI.

        This method is responsible for handling user changes in GUI and is used
        internally by Qt.
        """
        annotation = self.annotations[index.row()]
        if role == Qt.EditRole:
            column = self.annotations_column_names[index.column()]
            if column in [
                    constants.COL_BEGIN_TIME,
                    constants.COL_END_TIME,
                    constants.COL_LOW_FREQ,
                    constants.COL_HIGH_FREQ,
            ]:
                try:
                    value = utils.float_convert(value)
                except ValueError:
                    warnings.warn("Changed value should be a real number.")
                    return False

            if column == constants.COL_BEGIN_TIME:
                if value < annotation.time_end:
                    annotation.time_start = value
                    self._spectrogram_model.signal_visible_annotations()
                else:
                    warnings.warn("Begin Time (s) should be smaller than End Time (s)")
            elif column == constants.COL_END_TIME:
                if value > annotation.time_start:
                    annotation.time_end = value
                    self._spectrogram_model.signal_visible_annotations()
                else:
                    warnings.warn("Begin Time (s) should be smaller than End Time (s)")
            elif column == constants.COL_HIGH_FREQ:
                if value > annotation.freq_start:
                    annotation.freq_end = value
                    self._spectrogram_model.signal_visible_annotations()
                else:
                    warnings.warn("Low Freq (Hz) should be smaller than High Freq (Hz)")
            elif column == constants.COL_LOW_FREQ:
                if value < annotation.freq_end:
                    annotation.freq_start = value
                    self._spectrogram_model.signal_visible_annotations()
                else:
                    warnings.warn("Low Freq (Hz) should be smaller than High Freq (Hz)")
            elif column not in [constants.COL_DETECTION_METHOD]:
                annotation.table_data[column] = value

            return True
        if role == Qt.CheckStateRole:
            if value == Qt.CheckState.Unchecked:
                self.check_annotation(index.row(), False)
            elif value == Qt.CheckState.Checked:
                self.check_annotation(index.row(), True)

            return True

        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Set the headers to be displayed.

        Used internally by Qt.
        """
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
        """Define actions possible on the table.

        Used internally by Qt.
        """
        return (Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable |
                Qt.ItemIsUserCheckable)

    @property
    def annotations(self) -> List[Annotation]:
        return self._annotations

    @annotations.setter
    def annotations(self, annotations):
        if len(self.annotations) > 0:
            self.beginRemoveRows(QModelIndex(), 0, len(self.annotations) - 1)
            del self.annotations[:]
            self.endRemoveRows()

        self.append_annotations(annotations)

    def append_annotations(self, data):
        """Append rows into the model."""
        self.beginInsertRows(
            QModelIndex(),
            len(self.annotations),
            len(self.annotations) + len(data) - 1,
        )
        self._annotations += data
        self.endInsertRows()
        return True

    def update_selected_field(self, row, column):
        self.dataChanged.emit(self.index(row, column), self.index(row, column))

    def update_selected_column(self, column):
        self.dataChanged.emit(self.index(0, column),
                              self.index(self.rowCount(), column))

    def update_all_displayed_data(self):
        self.dataChanged.emit(self.index(0, 0),
                              self.index(self.rowCount() - 1, self.columnCount() - 1))

    @property
    def annotations_column_names(self):
        return self._annotations_column_names

    @annotations_column_names.setter
    def annotations_column_names(self, annotations_column_names):
        if len(self.annotations_column_names) > 0:
            self.beginRemoveColumns(QModelIndex(),
                                    0,
                                    len(self.annotations_column_names) - 1)
            del self._annotations_column_names[:]
            self.endRemoveColumns()

        self.update_annotations_column_names(annotations_column_names)

    def update_annotations_column_names(self, new_columns):
        # Make sure that column is not yet present.
        new_columns = list(
            filter(lambda x: x not in self.annotations_column_names, new_columns))
        self.beginInsertColumns(
            QModelIndex(),
            len(self.annotations_column_names),
            len(self.annotations_column_names) + len(new_columns) - 1,
        )
        self._annotations_column_names += new_columns
        self.endInsertColumns()

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

    def check_annotation(self, row, state):
        if not self.annotations[row].checked == state:
            self.annotations[row].checked = state
            if state:
                self.checked_annotations_counter += 1
            else:
                self.checked_annotations_counter -= 1
