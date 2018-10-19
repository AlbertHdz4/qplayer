from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
import utils
from variables import VariablesModel

import numpy as np


class RoutinesModel(QStandardItemModel):
    def __init__(self, variables_model:VariablesModel):
        super().__init__()
        self.variables_model = variables_model
        self.dataChanged.connect(self.update_values)

    def add_routine(self, name, channels):
        new_item = QStandardItem(name)

        for chan in channels:
            track_item = self._init_track_item(chan)
            new_item.appendRow(track_item)

        self.appendRow(new_item)
        index = new_item.index()
        self.dataChanged.emit(index,index)
        return new_item

    def add_event(self,routine: QStandardItem ,event: QStandardItem):
        routine.appendRow(event)

    def get_routine_names(self):
        names = []
        num_routines = self.rowCount()
        for i in range(num_routines):
            name = self.index(i,0).data(Qt.DisplayRole)
            names.append(name)
        return names

    @staticmethod
    def _init_track_item(chan):
        track_item = QStandardItem(chan.name)
        track_item.setData(chan.card.type, utils.TrackTypeRole)
        track_item.setData(chan, utils.ChannelRole)
        track_item.setData("0", utils.TrackOffsetRole)
        return track_item

    # Adds missing channels to a routine and removes the inactive ones
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
                track_item = self._init_track_item(chan)
                routine_item.appendRow(track_item)

        self.dataChanged.emit(routine_index, routine_index)

    def get_routine_duration(self, routine_name):
        #TODO:
        return 5

    @pyqtSlot()
    def update_values(self):
        # First we block signals because update_values is called on dataChanged and we don't want to trigger it again
        self.blockSignals(True)

        variables = self.variables_model.get_variables_dict()
        # __builtins__ is added so eval treats 'variables' as we want
        # (it doesn't add the builtin python variables)
        variables["__builtins__"] = {}

        # Make numpy available
        variables['np'] = np

        num_routines = self.rowCount()
        for r in range(num_routines):
            routine_index = self.index(r,0)
            num_channels = self.rowCount(routine_index)
            for c in range(num_channels):
                channel_index = self.index(c,0,routine_index)
                start = channel_index.data(utils.TrackOffsetRole)
                try:
                    start_time = float(start)
                except ValueError:
                    start_time = eval(start, variables)
                except TypeError:
                    if start is None:
                        start_time = 0
                num_events = self.rowCount(channel_index)
                for e in range(num_events):
                    event_index = self.index(e,0,channel_index)
                    self.setData(event_index,start_time,utils.EventStartRole)
                    duration = event_index.data(utils.EventDurationRole)
                    try:
                        start_time += float(duration)
                        self.itemFromIndex(event_index).setBackground(Qt.white)
                    except ValueError:
                        try:
                            start_time += eval(duration, variables)
                            self.itemFromIndex(event_index).setBackground(Qt.white)
                        except (SyntaxError, NameError):
                            color = QColor()
                            color.setNamedColor("#ffc5c7")
                            self.itemFromIndex(event_index).setBackground(color)
                        except TypeError:
                            print(duration)
                            print(variables)


        self.blockSignals(False)