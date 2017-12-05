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
