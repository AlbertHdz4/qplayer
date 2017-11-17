from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
import util

from random import randint


class RoutinesModel(QStandardItemModel):
    def __init__(self):
        super().__init__()

    def add_routine(self, name):
        new_item = QStandardItem(name)

        for i in range(8):
            track_item = QStandardItem("D%d"%i)
            track_item.setData(util.DigitalTrack,util.TrackTypeRole)
            new_item.appendRow(track_item)

            for j in range(randint(0,10)):
                event_item = QStandardItem()
                event_item.setData("%d"%randint(0,1000),Qt.DisplayRole)
                track_item.appendRow(event_item)

        for i in range(2):
            track_item = QStandardItem("A%d"%i)
            track_item.setData(util.AnalogTrack, util.TrackTypeRole)
            new_item.appendRow(track_item)

        self.appendRow(new_item)
        index = new_item.index()
        self.dataChanged.emit(index,index)
        return index