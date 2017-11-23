from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
import utils

from random import randint


class RoutinesModel(QStandardItemModel):
    def __init__(self):
        super().__init__()

    def add_routine(self, name, channels):
        new_item = QStandardItem(name)

        for chan in channels:
            track_item = QStandardItem(chan.name)
            track_item.setData(chan.card.track_type, utils.TrackTypeRole)
            track_item.setData(chan,utils.ChannelRole)
            new_item.appendRow(track_item)

        self.appendRow(new_item)
        index = new_item.index()
        self.dataChanged.emit(index,index)
        return index
