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
            track_item.setData(chan.card.type, utils.TrackTypeRole)
            track_item.setData(chan,utils.ChannelRole)
            new_item.appendRow(track_item)

        self.appendRow(new_item)
        index = new_item.index()
        self.dataChanged.emit(index,index)
        return index

    def set_active_channels(self, routine_index:QModelIndex, active_channels):

        currently_active_chans = []
        routine_item = self.itemFromIndex(routine_index)

        # remove inactive channels
        for j in reversed(range(self.rowCount(routine_index))):  # list is reversed for remove to work in order
            chan_index = self.index(j,0,routine_index)
            chan = self.data(chan_index,utils.ChannelRole)
            if chan not in active_channels:
                self.removeRow(j,routine_index)
            else:
                currently_active_chans.append(chan)

        # add missing active channels
        for chan in active_channels:
            if chan not in currently_active_chans:
                track_item = QStandardItem(chan.name)
                track_item.setData(chan.card.type, utils.TrackTypeRole)
                track_item.setData(chan, utils.ChannelRole)
                routine_item.appendRow(track_item)

        self.dataChanged.emit(routine_index, routine_index)

