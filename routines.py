from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
import utils
from variables import VariablesModel
from hardware import Hardware

import numpy as np


class RoutinesModel(QStandardItemModel):

    cleared = pyqtSignal()

    def __init__(self, variables_model: VariablesModel, hardware: Hardware):
        super().__init__()
        self.variables_model = variables_model
        self.hardware = hardware # type: Hardware
        self.cards = self.hardware.get_cards()
        self.dataChanged.connect(self.update_values)

    def clear(self):
        self.cleared.emit()
        self.removeRows(0, self.rowCount())

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
    def init_analog_event_item(event_item: QStandardItem, **kwargs):
        if event_item is None:
            event_item = QStandardItem()
        if len(kwargs) == 0:
            event_item.setData("0", utils.EventDurationRole)
            event_item.setData("constant", utils.AEventFunctionRole)
            event_item.setData("0", utils.AEventValueRole)

        for key, value in kwargs.items():
            if key == "duration":
                event_item.setData(value, utils.EventDurationRole)
            elif key == "function":
                event_item.setData(value, utils.AEventFunctionRole)
            elif key == "val":
                event_item.setData(value, utils.AEventValueRole)
            elif key == "start_val":
                event_item.setData(value, utils.AEventStartValRole)
            elif key == "end_val":
                event_item.setData(value, utils.AEventEndValRole)
            elif key == "gamma":
                event_item.setData(value, utils.AEventGammaRole)
            elif key == "frequency":
                event_item.setData(value, utils.AEventFrequencyRole)
            elif key == "phase":
                event_item.setData(value, utils.AEventPhaseRole)
            elif key == "amplitude":
                event_item.setData(value, utils.AEventAmplitudeRole)
            elif key == "offset":
                event_item.setData(value, utils.AEventOffsetRole)
            else:
                raise utils.SequenceException("Parameter '%s' not recognized"%key)

        return event_item

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
            duration = max(duration, channel_duration)
        return duration

    # Returns a dict representing the named routine in which the variables have been replaced by their numerical values.
    # The dict has the structure key->{'offset':num, 'events':[], 'chan':cards.Channel} where key is a pair  (card, chan_num)
    # TODO: delete get_routine_points
    def compile_routine(self, routine_name):
        points = {}

        variables = self.variables_model.get_variables_dict()
        # __builtins__ is added so eval treats 'variables' as we want
        # (it doesn't add the builtin python variables)
        variables["__builtins__"] = {}

        # Make numpy available
        variables['np'] = np

        routine_item = self.get_routine_item_by_name(routine_name)
        num_tracks = routine_item.rowCount()
        for c in range(num_tracks):
            track_item = routine_item.child(c)
            chan = track_item.data(utils.ChannelRole)
            chan_dict = chan.get_channel_dict()
            chan_key = (chan_dict['card'], chan_dict['index'])
            track_offset = eval(track_item.data(utils.TrackOffsetRole), variables)

            points[chan_key] = {"offset": track_offset, "events": [], "chan": chan}
            for k in range(track_item.rowCount()):
                event_item = track_item.child(k)
                event_duration = eval(event_item.data(utils.EventDurationRole), variables)

                if track_item.data(utils.TrackTypeRole) == utils.DigitalTrack:
                    event_state = int(event_item.data(Qt.CheckStateRole) == Qt.Checked)
                    points[chan_key]['events'].append({'type': 'boolean',
                                                       'duration': event_duration,
                                                       'state': event_state })

                elif track_item.data(utils.TrackTypeRole) == utils.AnalogTrack:
                    if event_item.data(utils.AEventFunctionRole) == 'constant':
                        value = eval(event_item.data(utils.AEventValueRole), variables)
                        points[chan_key]['events'].append({'type': 'constant',
                                                           'duration': event_duration,
                                                           'value': value})
                    elif event_item.data(utils.AEventFunctionRole) == 'linear':
                        start_val = eval(event_item.data(utils.AEventStartValRole), variables)
                        end_val = eval(event_item.data(utils.AEventEndValRole), variables)
                        points[chan_key]['events'].append({'type': 'linear',
                                                           'duration': event_duration,
                                                           'start_val': start_val,
                                                           'end_val': end_val})
                    elif event_item.data(utils.AEventFunctionRole) == 'exp':
                        start_val = eval(event_item.data(utils.AEventStartValRole), variables)
                        end_val = eval(event_item.data(utils.AEventEndValRole), variables)
                        gamma = eval(event_item.data(utils.AEventGammaRole), variables)
                        points[chan_key]['events'].append({'type': 'exp',
                                                           'duration': event_duration,
                                                           'start_val': start_val,
                                                           'end_val': end_val,
                                                           'gamma': gamma})

                    elif event_item.data(utils.AEventFunctionRole) == 'sin':
                        frequency = eval(event_item.data(utils.AEventFrequencyRole), variables)
                        amplitude = eval(event_item.data(utils.AEventAmplitudeRole), variables)
                        offset = eval(event_item.data(utils.AEventOffsetRole), variables)
                        phase = eval(event_item.data(utils.AEventPhaseRole), variables)
                        points[chan_key]['events'].append({'type': 'sin',
                                                           'duration': event_duration,
                                                           'frequency': frequency,
                                                           'amplitude': amplitude,
                                                           'offset': offset,
                                                           'phase': phase})

                    # TODO other function

        return points

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
                        ftype = event['function']
                        duration = event['duration']
                        if ftype == 'constant':
                            track_event = self.init_analog_event_item(None, function=ftype, val=event['val'], duration=duration)
                        elif ftype == 'linear':
                            track_event = self.init_analog_event_item(None, function=ftype,
                                                                      start_val=event['start_val'],
                                                                      end_val=event['end_val'],
                                                                      duration=duration)
                        elif ftype == 'exp':
                            track_event = self.init_analog_event_item(None, function=ftype,
                                                                      start_val=event['start_val'],
                                                                      end_val=event['end_val'],
                                                                      gamma=event['gamma'],
                                                                      duration=duration)
                        elif ftype == 'sin':
                            track_event = self.init_analog_event_item(None, function=ftype,
                                                                      frequency=event['frequency'],
                                                                      amplitude=event['amplitude'],
                                                                      offset=event['offset'],
                                                                      phase=event['phase'],
                                                                      duration=duration)
                        else:
                            raise utils.SequenceException('Unknown function type: %s'%ftype)
                        track_item.appendRow(track_event)

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
                        ftype = event_item.data(utils.AEventFunctionRole)
                        parsed_event['function'] = ftype
                        if ftype == "constant":
                            parsed_event['val'] = event_item.data(utils.AEventValueRole)
                        elif ftype == "linear":
                            parsed_event['start_val'] = event_item.data(utils.AEventStartValRole)
                            parsed_event['end_val'] = event_item.data(utils.AEventEndValRole)
                        elif ftype == "exp":
                            parsed_event['start_val'] = event_item.data(utils.AEventStartValRole)
                            parsed_event['end_val'] = event_item.data(utils.AEventEndValRole)
                            parsed_event['gamma'] = event_item.data(utils.AEventGammaRole)
                        elif ftype == "sin":
                            parsed_event['frequency'] = event_item.data(utils.AEventFrequencyRole)
                            parsed_event['amplitude'] = event_item.data(utils.AEventAmplitudeRole)
                            parsed_event['offset'] = event_item.data(utils.AEventOffsetRole)
                            parsed_event['phase'] = event_item.data(utils.AEventPhaseRole)
                    parsed_events.append(parsed_event)
                parsed_track["events"] = parsed_events
                parsed_tracks.append(parsed_track)
            parsed_routines[routine_name] = parsed_tracks

        return parsed_routines

    @pyqtSlot()
    def update_values(self):
        value_changed = False # Flag to decide if dataChanged signal should be emited

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
                    if start_time != self.data(event_index, utils.EventStartRole):
                        self.setData(event_index, start_time, utils.EventStartRole)
                        value_changed = True
                    duration = event_index.data(utils.EventDurationRole)
                    try:
                        dur_num = float(duration) # duration of event
                        self.setData(event_index, dur_num, utils.EventDurationRoleNum)
                        start_time += dur_num #Start time of next event
                        self.itemFromIndex(event_index).setBackground(Qt.white)
                    except ValueError:
                        try:
                            dur_num = eval(duration, variables) # duration of event
                            self.setData(event_index, dur_num, utils.EventDurationRoleNum)
                            start_time += dur_num  #Start time of next event
                            self.itemFromIndex(event_index).setBackground(Qt.white)
                        except (SyntaxError, NameError):
                            color = QColor("#ffc5c7")
                            self.itemFromIndex(event_index).setBackground(color)
                        except TypeError:
                            print(duration)
                            print(variables)
                    except TypeError: # in case duration in None
                        print("Error duration is: %s"%duration)

                    # Validate event parameters
                    if channel_index.data(utils.TrackTypeRole) == utils.AnalogTrack:
                        # ToDo: Validate other types of events
                        if event_index.data(utils.AEventFunctionRole) == "constant":
                            value = event_index.data(utils.AEventValueRole)
                            try:
                                val = eval(value, variables)
                                if event_index.data(utils.AEventValueNumericRole) != val:
                                    self.setData(event_index, val, utils.AEventValueNumericRole)
                                    value_changed = True
                                card = channel_index.data(utils.ChannelRole).card
                                if val > card.vmax() or val < card.vmin():
                                    self.itemFromIndex(event_index).setData(QColor("#f7df97"), utils.AEventValueBackgroundRole)
                                else:
                                    self.itemFromIndex(event_index).setData(QColor("#ffffff"), utils.AEventValueBackgroundRole)
                            except (SyntaxError, NameError):
                                self.itemFromIndex(event_index).setData(QColor("#ffc5c7"), utils.AEventValueBackgroundRole)


                # There is no next event so start_time contains the duration of this channel
                if start_time != self.data(channel_index, utils.ChannelDurationRole):
                    value_changed = True
                    self.setData(channel_index,start_time, utils.ChannelDurationRole)

        self.blockSignals(False)
        if value_changed:
            self.dataChanged.emit(QModelIndex(),QModelIndex())
            # ToDo: maybe it's more efficient to call dataChanged for each QModelIndex that was changed