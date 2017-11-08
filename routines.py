from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont


class RoutinesModel(QStandardItemModel):
    def __init__(self):
        super().__init__()

    def add_routine(self, name):
        new_item = QStandardItem(name)
        self.appendRow(new_item)
        self.dataChanged.emit(QModelIndex(),QModelIndex())