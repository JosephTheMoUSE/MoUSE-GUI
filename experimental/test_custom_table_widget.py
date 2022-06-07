from random import shuffle
from PySide6 import QtCore, QtWidgets

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        super(TableModel, self).__init__(parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._data[0]) if self.rowCount() else 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            if 0 <= row < self.rowCount():
                column = index.column()
                if 0 <= column < self.columnCount():
                    return self._data[row][column]

class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.table = QtWidgets.QTableView(self)
        self.tablewidget = QtWidgets.QTableWidget(self)
        self.tablewidget.setSortingEnabled(True)
        self.button1 = QtWidgets.QPushButton('Custom Model', self)
        self.button1.clicked.connect(
            lambda: self.populateTable('custom'))
        self.button2 = QtWidgets.QPushButton('StandardItem Model', self)
        self.button2.clicked.connect(
            lambda: self.populateTable('standard'))
        self.button3 = QtWidgets.QPushButton('TableWidget', self)
        self.button3.clicked.connect(
            lambda: self.populateTable('widget'))
        self.spinbox = QtWidgets.QSpinBox(self)
        self.spinbox.setRange(15000, 1000000)
        self.spinbox.setSingleStep(10000)
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.table, 0, 0, 1, 4)
        layout.addWidget(self.tablewidget, 1, 0, 1, 4)
        layout.addWidget(self.button1, 2, 0)
        layout.addWidget(self.button2, 2, 1)
        layout.addWidget(self.button3, 2, 2)
        layout.addWidget(self.spinbox, 2, 3)
        self._data = []

    def populateTable(self, mode):
        if mode == 'widget':
            self.tablewidget.clear()
            self.tablewidget.setRowCount(self.spinbox.value())
            self.tablewidget.setColumnCount(20)
        else:
            model = self.table.model()
            if model is not None:
                self.table.setModel(None)
                model.deleteLater()
        if len(self._data) != self.spinbox.value():
            del self._data[:]
            rows = list(range(self.spinbox.value()))
            shuffle(rows)
            for row in rows:
                items = []
                for column in range(20):
                    items.append('(%d, %d)' % (row, column))
                self._data.append(items)
        timer = QtCore.QElapsedTimer()
        timer.start()
        if mode == 'widget':
            self.tablewidget.setSortingEnabled(False)
            for row, items in enumerate(self._data):
                for column, text in enumerate(items):
                    item = QtWidgets.QTableWidgetItem(text)
                    self.tablewidget.setItem(row, column, item)
            self.tablewidget.sortByColumn(0, QtCore.Qt.AscendingOrder)
        else:
            self.table.setSortingEnabled(False)
            if mode == 'custom':
                model = TableModel(self._data, self.table)
            elif mode == 'standard':
                model = QtWidgets.QStandardItemModel(self.table)
                for row in self._data:
                    items = []
                    for column in row:
                        items.append(QtWidgets.QStandardItem(column))
                    model.appendRow(items)
            self.table.setModel(model)
            self.table.setSortingEnabled(True)
            self.table.sortByColumn(0, QtCore.Qt.AscendingOrder)
        print('%s: %.3g seconds' % (mode, timer.elapsed() / 1000))

if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Window()
    window.setGeometry(600, 50, 1200, 800)
    window.show()
    sys.exit(app.exec_())