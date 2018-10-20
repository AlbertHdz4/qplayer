from PyQt5.QtCore import Qt, QModelIndex, QIdentityProxyModel, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
import utils
from routines import RoutinesModel


class PlaylistModel(QStandardItemModel):
    def __init__(self, routines_model: RoutinesModel):
        super().__init__()
        self.routines_model = routines_model
        self.setHorizontalHeaderLabels(["routine", "start", "duration", "end"])
        self.dataChanged.connect(self.update_values)

    def flags(self, index: QModelIndex):
        return Qt.NoItemFlags | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def add_playlist(self, playlist_name, start_time, duration, end_time):
        playlist_name_item = QStandardItem(playlist_name)
        font = QFont()
        font.setBold(True)
        playlist_name_item.setData(font,Qt.FontRole)

        playlist_item = [playlist_name_item,
                         QStandardItem(start_time),
                         QStandardItem(duration),
                         QStandardItem(end_time)]
        self.invisibleRootItem().appendRow(playlist_item)
        self.dataChanged.emit(QModelIndex(), QModelIndex())
        # TODO: ensure unique names

    def add_playlist_item(self,parent,name):
        item_name = QStandardItem(name)
        item_name.setData(utils.Routine,utils.PlaylistItemTypeRole)

        item_start = QStandardItem("start time")
        item_duration = QStandardItem("duration")
        item_end = QStandardItem("end time")

        new_row = [item_name, item_start, item_duration, item_end]
        self.itemFromIndex(parent).appendRow(new_row)
        self.dataChanged.emit(parent,parent)

    def add_gap(self, parent, duration):
        item_name = QStandardItem("Gap")
        item_name.setData(utils.Gap, utils.PlaylistItemTypeRole)

        item_start = QStandardItem("start time")
        item_duration = QStandardItem(duration)
        item_end = QStandardItem("end time")

        new_row = [item_name, item_start, item_duration, item_end]
        self.itemFromIndex(parent).appendRow(new_row)
        self.dataChanged.emit(parent, parent)

    def modify_gap(self, index, duration):
        item = self.itemFromIndex(index)
        item.parent().child(item.row(), 2).setData(duration, Qt.DisplayRole)

    def move_branch(self,index_to_move,new_parent_index):
        new_parent_item = self.itemFromIndex(new_parent_index)
        parent_of_item_to_move = self.itemFromIndex(index_to_move.parent())
        item_to_move = parent_of_item_to_move.takeRow(index_to_move.row())
        new_parent_item.appendRow(item_to_move)
        self.dataChanged.emit(QModelIndex(), QModelIndex())


    def rename_playlist(self, index, new_name):
        item = self.itemFromIndex(index)
        item.setData(new_name, Qt.DisplayRole)
        # TODO: ensure unique names

    def get_playlists_names(self):
        names = []
        num_playlists = self.rowCount()
        for i in range(num_playlists):
            name = self.index(i,0).data(Qt.DisplayRole)
            names.append(name)
        return names

    @pyqtSlot()
    def update_values(self):
        # First we block signals because update_values is called on dataChanged and we don't want to trigger it again
        self.blockSignals(True)

        for item in utils.iter_tree_rows(self.invisibleRootItem()): # type: QStandardItem
            if item.parent() is not None: # This will be true for a routine and false for a playlist, which all are a root elements
                if item.parent().parent() is None: # This will only be true for top-level routines which begin the sequence
                    if item.data(utils.PlaylistItemTypeRole) == utils.Routine:
                        routine_name = item.data(Qt.DisplayRole)
                        routine_duration = self.routines_model.get_routine_duration(routine_name)

                        item.parent().child(item.row(), 1).setData(0, Qt.DisplayRole)
                        item.parent().child(item.row(), 2).setData(routine_duration, Qt.DisplayRole)
                        item.parent().child(item.row(), 3).setData(routine_duration, Qt.DisplayRole)
                    elif item.data(utils.PlaylistItemTypeRole) == utils.Gap:
                        gap_duration = item.parent().child(item.row(), 2).data(Qt.DisplayRole)

                        item.parent().child(item.row(), 1).setData(0, Qt.DisplayRole)
                        item.parent().child(item.row(), 3).setData(gap_duration, Qt.DisplayRole)


                else: #Non top-level routines
                    parent = item.parent()
                    parent_end_time = parent.parent().child(parent.row(), 3).data(Qt.DisplayRole)

                    if item.data(utils.PlaylistItemTypeRole) == utils.Routine: #if item is a routine
                        routine_name = item.data(Qt.DisplayRole)
                        routine_duration = self.routines_model.get_routine_duration(routine_name)

                        item.parent().child(item.row(), 1).setData(parent_end_time, Qt.DisplayRole)
                        item.parent().child(item.row(), 2).setData(routine_duration, Qt.DisplayRole)
                        item.parent().child(item.row(), 3).setData(float(parent_end_time)+routine_duration, Qt.DisplayRole)
                    elif item.data(utils.PlaylistItemTypeRole) == utils.Gap:
                        gap_duration = item.parent().child(item.row(), 2).data(Qt.DisplayRole)
                        print(gap_duration)

                        item.parent().child(item.row(), 1).setData(parent_end_time, Qt.DisplayRole)
                        #TODO: breaks with symbolic gap
                        item.parent().child(item.row(), 3).setData(float(parent_end_time)+float(gap_duration), Qt.DisplayRole)

        self.blockSignals(False)

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

