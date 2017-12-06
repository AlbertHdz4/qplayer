from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
import utils
from routines import RoutinesModel



class PlaylistModel(QStandardItemModel):
    def __init__(self, routines_model: RoutinesModel):
        super().__init__()
        self.routines_model = routines_model

        visible_root_item = QStandardItem("Sequence start")

        self.invisibleRootItem().appendRow(visible_root_item)

    def add_playlist_item(self,parent,name):
        new_row = QStandardItem(name)
        new_row.setData(utils.Routine,utils.PlaylistItemTypeRole)
        self.itemFromIndex(parent).appendRow(new_row)

    def add_gap(self, parent, duration):
        new_row = QStandardItem("Gap: "+duration)
        new_row.setData(utils.Gap, utils.PlaylistItemTypeRole)
        new_row.setData(duration, utils.GapDurationRole)
        self.itemFromIndex(parent).appendRow(new_row)

    def modify_gap(self, index, duration):
        item = self.itemFromIndex(index)
        item.setData("Gap: "+duration, Qt.DisplayRole)
        item.setData(duration,utils.GapDurationRole)

