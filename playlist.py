from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel, pyqtSlot
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
        return Qt.NoItemFlags | Qt.ItemIsEnabled

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
        new_row = QStandardItem("Gap: "+duration)
        new_row.setData(utils.Gap, utils.PlaylistItemTypeRole)
        new_row.setData(duration, utils.GapDurationRole)
        self.itemFromIndex(parent).appendRow(new_row)
        self.dataChanged.emit(parent, parent)

    def modify_gap(self, index, duration):
        item = self.itemFromIndex(index)
        item.setData("Gap: "+duration, Qt.DisplayRole)
        item.setData(duration,utils.GapDurationRole)

    def rename_playlist(self, index, new_name):
        item = self.itemFromIndex(index)
        item.setData(new_name, Qt.DisplayRole)
        # TODO: ensure unique names

    @pyqtSlot()
    def update_values(self):
        # First we block signals because update_values is called on dataChanged and we don't want to trigger it again
        self.blockSignals(True)

        for item in utils.iter_tree_rows(self.invisibleRootItem()): # type: QStandardItem
            #if item.hasChildren():
            print(item.data(Qt.DisplayRole))

        self.blockSignals(False)