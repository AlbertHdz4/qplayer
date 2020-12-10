from PyQt5.QtCore import Qt, QModelIndex, QIdentityProxyModel, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
import utils
from routines import RoutinesModel
from variables import VariablesModel
import numpy as np


class PlaylistModel(QStandardItemModel):

    column_names = ["routine", "start", "repeat", "duration", "end"]

    def __init__(self, variables_model: VariablesModel, routines_model: RoutinesModel):
        super().__init__()
        self.variables_model = variables_model
        self.routines_model = routines_model
        self.setHorizontalHeaderLabels(self.column_names)
        self.dataChanged.connect(self.update_values)
        self.active_playlist = None

    def flags(self, index: QModelIndex):
        return Qt.NoItemFlags | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def add_playlist(self, playlist_name, start_time, repeat, duration, end_time):
        playlist_name_item = QStandardItem(playlist_name)
        font = QFont()
        font.setBold(True)
        playlist_name_item.setData(font,Qt.FontRole)

        # TODO: ensure unique names
        playlist_item = [playlist_name_item,
                         QStandardItem(start_time),
                         QStandardItem(repeat),
                         QStandardItem(duration),
                         QStandardItem(end_time)]
        self.invisibleRootItem().appendRow(playlist_item)
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        num_rows = self.rowCount()
        return self.index(num_rows - 1, 0)

    def add_playlist_item(self,parent,name,repeat=1):
        item_name = QStandardItem(name)
        item_name.setData(utils.Routine,utils.PlaylistItemTypeRole)

        item_start = QStandardItem("start time")
        item_repeat = QStandardItem(str(repeat))
        item_duration = QStandardItem("duration")
        item_end = QStandardItem("end time")

        new_row = [item_name, item_start, item_repeat, item_duration, item_end]
        self.itemFromIndex(parent).appendRow(new_row)
        self.dataChanged.emit(parent,parent)
        num_rows = self.rowCount(parent)
        return self.index(num_rows - 1,0,parent)

    def add_gap(self, parent, duration):
        item_name = QStandardItem("Gap")
        item_name.setData(utils.Gap, utils.PlaylistItemTypeRole)

        item_start = QStandardItem("start time")
        item_repeat = QStandardItem("-")
        item_duration = QStandardItem(duration)
        item_end = QStandardItem("end time")

        new_row = [item_name, item_start, item_repeat, item_duration, item_end]
        self.itemFromIndex(parent).appendRow(new_row)
        self.dataChanged.emit(parent, parent)
        num_rows = self.rowCount(parent)
        return self.index(num_rows - 1,0,parent)


    def modify_gap(self, index, duration):
        item = self.itemFromIndex(index)
        item.parent().child(item.row(), self.column_names.index("duration")).setData(duration, Qt.DisplayRole)

    def move_branch(self,index_to_move,new_parent_index):
        new_parent_item = self.itemFromIndex(new_parent_index)
        parent_of_item_to_move = self.itemFromIndex(index_to_move.parent())
        item_to_move = parent_of_item_to_move.takeRow(index_to_move.row())
        new_parent_item.appendRow(item_to_move)
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def rename_playlist(self, index, new_name):
        item = self.itemFromIndex(index)
        if new_name in self.get_playlists_names():
            raise utils.SequenceException("Playlist names must be unique")
        else:
            item.setData(new_name, Qt.DisplayRole)

    def get_playlists_names(self):
        names = []
        num_playlists = self.rowCount()
        for i in range(num_playlists):
            name = self.index(i,0).data(Qt.DisplayRole)
            names.append(name)
        return names

    def load_playlist_from_pystruct(self, playlist_list):

        def inner_add_children(parent_index, children_dict):
            for child in children_dict:
                if child['type'] == utils.Gap:
                    newindex = self.add_gap(parent_index, child['duration'])
                elif child['type'] == utils.Routine:
                    newindex = self.add_playlist_item(parent_index, child['name'], child['repeat']) # type: QModelIndex
                inner_add_children(newindex,child['children'])

        while len(playlist_list) > 0:
            pldict = playlist_list.pop(0)
            plindex = self.add_playlist(pldict['name'], "0", "-", "-", "-")
            inner_add_children(plindex,pldict['children'])

    # Returns a python dictionary containing the playlist info por the purpose of saving to a file
    def get_playlist_pystruct(self):
        # This recursive function is use to travel through the tree
        def inner_get_parsed_playlist(children_items, children_list):
            for child_item in children_items: # type: QStandardItem
                child_row = child_item.row()
                child_type = child_item.data(utils.PlaylistItemTypeRole)
                child_children = [child_item.child(j) for j in range(child_item.rowCount())]
                # TODO: fix hardcoded repeat
                child_dict = {"type": child_type, "children": []}
                if child_type == utils.Gap:
                    child_duration = child_item.parent().child(child_row, self.column_names.index("duration")).data(Qt.DisplayRole)
                    child_dict["duration"] = child_duration
                elif child_type == utils.Routine:
                    child_name = child_item.data(Qt.DisplayRole)
                    child_repeat = child_item.parent().child(child_row, self.column_names.index("repeat")).data(Qt.DisplayRole)

                    child_dict["name"] = child_name
                    child_dict["repeat"] = child_repeat
                inner_get_parsed_playlist(child_children,child_dict["children"])
                children_list.append(child_dict)

        parsed_playlist = []
        for i in range(self.rowCount()):
            playlist_index = self.index(i,0)
            playlist_item = self.itemFromIndex(playlist_index)
            playlist_name = playlist_item.data(Qt.DisplayRole)
            playlist_dict = {"name": playlist_name,"children": []}
            playlist_children_items = [playlist_item.child(j) for j in range(playlist_item.rowCount())]
            inner_get_parsed_playlist(playlist_children_items, playlist_dict["children"])
            parsed_playlist.append(playlist_dict)

        return parsed_playlist

    @pyqtSlot()
    def update_values(self):

        value_changed = False  # Flag to decide if dataChanged signal should be emited

        # TODO add full playlist duration
        # First we block signals because update_values is called on dataChanged and we don't want to trigger it again
        self.blockSignals(True)

        variables = self.variables_model.get_variables_dict()
        # __builtins__ is added so eval treats 'variables' as we want
        # (it doesn't add the builtin python variables)
        variables["__builtins__"] = {}

        # Make numpy available
        variables['np'] = np

        for item in utils.iter_tree_rows(self.invisibleRootItem()): # type: QStandardItem
            if item.parent() is not None: # This will be true for a routine and false for a playlist, which all are a root elements
                if item.parent().parent() is None: # This will only be true for top-level routines which begin the sequence
                    if item.data(utils.PlaylistItemTypeRole) == utils.Routine:
                        routine_name = item.data(Qt.DisplayRole)
                        routine_duration = self.routines_model.get_routine_duration(routine_name)

                        if item.parent().child(item.row(), self.column_names.index("start")).data(Qt.DisplayRole) != "0":
                            item.parent().child(item.row(), self.column_names.index("start")).setData("0", Qt.DisplayRole)
                            value_changed = True

                        if item.parent().child(item.row(), self.column_names.index("duration")).data(Qt.DisplayRole) != "%g"%routine_duration:
                            item.parent().child(item.row(), self.column_names.index("duration")).setData("%g"%routine_duration, Qt.DisplayRole)
                            value_changed = True

                        if item.parent().child(item.row(), self.column_names.index("end")).data(Qt.DisplayRole) != "%g"%routine_duration:
                            item.parent().child(item.row(), self.column_names.index("end")).setData("%g"%routine_duration, Qt.DisplayRole)
                            value_changed = True

                    elif item.data(utils.PlaylistItemTypeRole) == utils.Gap:
                        gap_duration = item.parent().child(item.row(), self.column_names.index("duration")).data(Qt.DisplayRole)

                        if item.parent().child(item.row(), self.column_names.index("start")).data(Qt.DisplayRole) != '0':
                            item.parent().child(item.row(), self.column_names.index("start")).setData('0', Qt.DisplayRole)
                            value_changed = True

                        if item.parent().child(item.row(), self.column_names.index("end")).data(Qt.DisplayRole) != gap_duration:
                            item.parent().child(item.row(), self.column_names.index("end")).setData(gap_duration, Qt.DisplayRole)
                            value_changed = True

                else: # Non top-level routines
                    parent = item.parent()
                    parent_end_time = parent.parent().child(parent.row(), self.column_names.index("end")).data(Qt.DisplayRole)

                    if item.data(utils.PlaylistItemTypeRole) == utils.Routine: # if item is a routine
                        routine_name = item.data(Qt.DisplayRole)
                        routine_duration = self.routines_model.get_routine_duration(routine_name)

                        if item.parent().child(item.row(), self.column_names.index("start")).data(Qt.DisplayRole) != parent_end_time:
                            item.parent().child(item.row(), self.column_names.index("start")).setData(parent_end_time, Qt.DisplayRole)
                            value_changed = True

                        if item.parent().child(item.row(), self.column_names.index("duration")).data(Qt.DisplayRole) != "%g"%routine_duration:
                            item.parent().child(item.row(), self.column_names.index("duration")).setData("%g"%routine_duration, Qt.DisplayRole)
                            value_changed = True

                        try:
                            if item.parent().child(item.row(), self.column_names.index("end")).data(Qt.DisplayRole) != "%g"%(float(parent_end_time)+routine_duration):
                                item.parent().child(item.row(), self.column_names.index("end")).setData("%g"%(float(parent_end_time)+routine_duration), Qt.DisplayRole)
                                value_changed = True
                        except TypeError:
                            print('Argh!')
                            # TODO: give notice

                    elif item.data(utils.PlaylistItemTypeRole) == utils.Gap:
                        gap_duration = item.parent().child(item.row(), self.column_names.index("duration")).data(Qt.DisplayRole)

                        if item.parent().child(item.row(), self.column_names.index("start")).data(Qt.DisplayRole) != parent_end_time:
                            item.parent().child(item.row(), self.column_names.index("start")).setData(parent_end_time, Qt.DisplayRole)
                            value_changed = True

                        try:
                            if item.parent().child(item.row(), self.column_names.index("end")).data(Qt.DisplayRole) != "%g"%(float(parent_end_time)+float(gap_duration)):
                                item.parent().child(item.row(), self.column_names.index("end")).setData("%g"%(float(parent_end_time)+float(gap_duration)), Qt.DisplayRole)
                                value_changed = True
                        except ValueError:
                            gap_duration_time = eval(gap_duration, variables)
                            if item.parent().child(item.row(), self.column_names.index("end")).data(Qt.DisplayRole) != "%g"%(float(parent_end_time)+gap_duration_time):
                                item.parent().child(item.row(), self.column_names.index("end")).setData("%g"%(float(parent_end_time)+gap_duration_time), Qt.DisplayRole)
                                value_changed = True
                        except TypeError:
                            print('Argh!')
                            # TODO: give notice

        self.blockSignals(False)
        if value_changed:
            self.dataChanged.emit(QModelIndex(),QModelIndex())
            # ToDo: maybe it's more efficient to call dataChanged for each QModelIndex that was changed

    @pyqtSlot(int)
    def set_active_playlist(self, index):
        self.active_playlist = index

    # Returns  a dict with the states and times for each transition in all of the channels in the active playlist
    # where key is channel name and value is is a list of (time,state) pairs.
    def get_active_playlist_points(self):

        def inner_get_playlist_branch_points(routine_item : QStandardItem):
            points = {}
            tend = 0 # end time of current routine

            if routine_item.data(utils.PlaylistItemTypeRole) == utils.Routine:
                # find routine points relative to routine start

                routine_name = routine_item.data(Qt.DisplayRole)
                routine_points = self.routines_model.get_routine_points(routine_name)

                for chan in routine_points:
                    offset = routine_points[chan]["offset"]
                    events = routine_points[chan]["events"]

                    if chan not in points:
                        #points[chan] = [(offset, events[0][1])]
                        points[chan] = []
                    t = offset
                    if len(events) > 0:
                        for event in events:
                            time, state  = event[0], event[1]
                            points[chan].append((t, state))
                            t += time
                            tend = max(tend, t)
                        points[chan].append((t,state)) # the last point is added to know how long to hold the state for

            elif routine_item.data(utils.PlaylistItemTypeRole) == utils.Gap:
                # if gap has children add children points with gap delay added
                # else if gap is last in sequence add points at end with previous value (can this be even done with a recursive function?)
                # TODO
                pass

            for i in range(routine_item.rowCount()):
                child_item = routine_item.child(i)
                child_points = inner_get_playlist_branch_points(child_item)

                for chan in child_points:
                    if chan not in points:
                        points[chan] = []
                    for chan_point in child_points[chan]:
                        time, state = chan_point
                        points[chan].append((tend+time, state))

            return points
        if self.active_playlist is not None:
            active_pl_item = self.item(self.active_playlist) # type: QStandardItem
            return inner_get_playlist_branch_points(active_pl_item)
        else:
            return None


class PlaylistMoveRoutineProxyModel(QIdentityProxyModel): #Used for playlist move dialog
    def __init__(self, move_index: QModelIndex):
        super().__init__()
        self.move_index = move_index


    def flags(self, index: QModelIndex):

        src_index = self.mapToSource(index)

        if src_index.column() > 0:
            _flags = super().flags(index) & ~Qt.ItemIsEnabled
        elif utils.is_descendant_of(self.move_index,src_index) or self.move_index == src_index:
            _flags = Qt.NoItemFlags
        else:
            _flags = super().flags(index)
        return _flags

