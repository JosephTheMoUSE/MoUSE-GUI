import sys

from PySide6 import QtCore, QtGui, QtWidgets


class CustomDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        value = index.data(QtCore.Qt.CheckStateRole)
        if value is None:
            model = index.model()
            model.setData(index, QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
        super().initStyleOption(option, index)
        option.direction = QtCore.Qt.RightToLeft
        option.displayAlignment = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter


class Mainwindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.table = QtWidgets.QTableView()
        self.setCentralWidget(self.table)

        self.list = ["item_1", "item_2", "item_3"]
        self.data = [
            [1, "Blocks γ=500 GOST 31359-2007", self.list[0], 0.18, 0.22],
            [2, "Blocks γ=600 GOST 31359-2008", self.list[0], 0.25, 0.27],
            [3, "Insulation", self.list[0], 0.041, 0.042],
            [3, "Insulation", self.list[0], 0.041, 0.042],
        ]

        self.model = Materials(self.data)
        self.table.setModel(self.model)

        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)

        for row in range(len(self.model.materials)):
            index = self.table.model().index(row, 2)
            self.table.setIndexWidget(index, self.setting_combobox(index))

        delegate = CustomDelegate(self.table)
        self.table.setItemDelegateForColumn(4, delegate)

        self.resize(640, 480)

    def setting_combobox(self, index):
        widget = QtWidgets.QComboBox()
        list = self.list
        widget.addItems(list)
        widget.setCurrentIndex(0)
        widget.currentTextChanged.connect(
            lambda value: self.model.setData(index, value)
        )
        return widget


class Materials(QtCore.QAbstractTableModel):
    def __init__(self, materials=[[]], parent=None):
        super(Materials, self).__init__()
        self.materials = materials

        self.check_states = dict()

    def rowCount(self, parent):
        return len(self.materials)

    def columnCount(self, parent):
        return len(self.materials[0])

    def data(self, index, role):

        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            column = index.column()
            value = self.materials[row][column]
            return value

        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            value = self.materials[row][column]
            return value

        if role == QtCore.Qt.FontRole:
            if index.column() == 0:
                boldfont = QtGui.QFont()
                boldfont.setBold(True)
                return boldfont

        if role == QtCore.Qt.CheckStateRole:
            value = self.check_states.get(QtCore.QPersistentModelIndex(index))
            if value is not None:
                return value

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            self.materials[row][column] = value
            self.dataChanged.emit(index, index, (role,))
            return True
        if role == QtCore.Qt.CheckStateRole:
            self.check_states[QtCore.QPersistentModelIndex(index)] = value
            self.dataChanged.emit(index, index, (role,))
            return True
        return False

    def flags(self, index):
        return (
            QtCore.Qt.ItemIsEditable
            | QtCore.Qt.ItemIsEnabled
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsUserCheckable
        )


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    application = Mainwindow()
    application.show()

    sys.exit(app.exec())