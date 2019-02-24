from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
import utils
from variables import VariablesModel

import numpy as np


class RoutinesModel(QStandardItemModel):
    def __init__(self, variables_model:VariablesModel, cards):
        super().__init__()
        self.variables_model = variables_model
        self.cards = cards
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

    #def add_event(self, routine: QStandardItem, event: QStandardItem):
    #    routine.appendRow(event)

    def get_routine_names(self):
        names = []
        num_routines = self.rowCount()
        for i in range(num_routines):
            name = self.index(i, 0).data(Qt.DisplayRole)
            names.append(name)
        return names

    @staticmethod
    def _init_track_item(chan, offset = "0"):
        track_item = QStandardItem(chan.name)
        track_item.setData(chan.card.type, utils.TrackTypeRole)
        track_item.setData(chan, utils.ChannelRole)
        track_item.setData(offset, utils.TrackOffsetRole)
        return track_item

    @staticmethod
    def init_digital_event_item(event_item: QStandardItem = None, data="0", checked=False):
        if event_item is None:
            event_item = QStandardItem()
        event_item.setCheckable(True)
        if checked:
            event_item.setCheckState(Qt.Checked)
        else:
            event_item.setCheckState(Qt.Unchecked)
        event_item.setData(data, utils.EventDurationRole)
        event_item.setBackground(Qt.white)
        return event_item

    @staticmethod
    def init_analog_event_item(event_item: QStandardItem):
        event_item.setData("0", utils.EventDurationRole)

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

    def get_routine_item_by_name(self, routine_name) -> QStandardItem:
        num_routines = self.rowCount()
        for i in range(num_routines):
            name = self.index(i,0).data(Qt.DisplayRole)
            if name == routine_name:
                return self.itemFromIndex(self.index(i,0))

        return None

    def get_routine_duration(self, routine_name):
        self.update_values()
        routine_item = self.get_routine_item_by_name(routine_name)
        num_channels = routine_item.rowCount()
        duration = 0
        for c in range(num_channels):
            channel_duration = 0
            channel_item = routine_item.child(c)
            channel_duration = channel_item.data(utils.ChannelDurationRole)
            duration = max(duration,channel_duration)
        return duration

    def load_routines_from_pystruct(self, routines_dict):
        routine_names = routines_dict.keys()
        for routine_name in routine_names:
            routine_item = QStandardItem(routine_name)

            routine = routines_dict[routine_name]
            for track in routine:
                card = self.cards[track["chan"]["card"]]
                index = track["chan"]["index"]
                offset = track["offset"]
                events = track["events"]
                chan = card.channels[index]
                track_item = self._init_track_item(chan, offset)
                routine_item.appendRow(track_item)
                if card.type == utils.DigitalTrack:
                    for event in events:
                        duration = event["duration"]
                        state = event["state"]
                        track_event = self.init_digital_event_item(None, duration, state)
                        track_item.appendRow(track_event)
                elif card.type == utils.AnalogTrack:
                    for event in events:
                        pass

            self.appendRow(routine_item)

    def get_routines_pystruct(self):
        parsed_routines  = {}
        for i in range(self.rowCount()):
            routine_index = self.index(i,0)
            routine_item = self.itemFromIndex(routine_index)
            routine_name = routine_index.data()
            parsed_tracks = []
            for j in range(routine_item.rowCount()):
                track_item = routine_item.child(j)
                track_name = track_item.data(Qt.DisplayRole)
                parsed_track = {}
                parsed_track["chan"] = track_item.data(utils.ChannelRole).get_channel_dict()
                parsed_track["offset"] = track_item.data(utils.TrackOffsetRole)

                parsed_events = []
                for k in range(track_item.rowCount()):
                    event_item = track_item.child(k)
                    event_duration = event_item.data(Qt.DisplayRole)
                    parsed_event = {"duration": event_duration}
                    if track_item.data(utils.TrackTypeRole) == utils.DigitalTrack:
                        parsed_event["state"] = (event_item.data(Qt.CheckStateRole) == Qt.Checked)
                    elif track_item.data(utils.TrackTypeRole) == utils.AnalogTrack:
                        #TODO
                        pass
                    parsed_events.append(parsed_event)
                parsed_track["events"] = parsed_events
                parsed_tracks.append(parsed_track)
            parsed_routines[routine_name] = parsed_tracks

        return parsed_routines

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
                        start_time += float(duration) #Start time of next event
                        self.itemFromIndex(event_index).setBackground(Qt.white)
                    except ValueError:
                        try:
                            start_time += eval(duration, variables) #Start time of next event
                            self.itemFromIndex(event_index).setBackground(Qt.white)
                        except (SyntaxError, NameError):
                            color = QColor()
                            color.setNamedColor("#ffc5c7")
                            self.itemFromIndex(event_index).setBackground(color)
                        except TypeError:
                            print(duration)
                            print(variables)
                    except TypeError: # in case duration in None
                        print("Error duration is:")
                        print(duration)

                # There is no next event so start_time contains the duration of this channel
                self.setData(channel_index,start_time,utils.ChannelDurationRole)


        self.blockSignals(False)