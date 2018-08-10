from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem

# User-defined role to use with QStandardItemModel
TrackTypeRole = Qt.UserRole + 1
ChannelRole = Qt.UserRole + 2
VariableTypeRole = Qt.UserRole + 3
EventStartRole = Qt.UserRole + 4
EventDurationRole = Qt.DisplayRole
TrackOffsetRole = Qt.UserRole + 6
PlaylistItemTypeRole = Qt.UserRole + 7
GapDurationRole = Qt.UserRole + 8

# TrackTypes
DigitalTrack = 0
AnalogTrack = 1

# VariableTypes
NumericVariable = 0
CodeVariable = 1

# Playlist item types
Routine = 0
Gap = 1

def iter_tree_rows(root: QStandardItem):
    if root is not None:
        stack = [root]
        while stack:
            parent = stack.pop(0)
            for row in range(parent.rowCount()):
                    child = parent.child(row)
                    yield child
                    if child.hasChildren():
                        stack.append(child)
