from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QStandardItem

# User-defined role to use with QStandardItemModel
TrackTypeRole = Qt.UserRole + 1 # Digital/Analog
ChannelRole = Qt.UserRole + 2 # An instance of cards.Channel
VariableTypeRole = Qt.UserRole + 3
EventStartRole = Qt.UserRole + 4
EventDurationRole = Qt.DisplayRole # set value for the duration of an event
EventDurationRoleNum = Qt.UserRole + 6 # numerical value for the duration of an event
TrackOffsetRole = Qt.UserRole + 7 # Time offset for the first event in the track
PlaylistItemTypeRole = Qt.UserRole + 8
GapDurationRole = Qt.UserRole + 9
ChannelDurationRole = Qt.UserRole + 10
AEventFunctionRole = Qt.UserRole + 11
AEventValueRole = Qt.UserRole + 12
AEventStartValRole = AEventValueRole
AEventEndValRole = Qt.UserRole + 13
AEventGammaRole = Qt.UserRole + 14
AEventAmplitudeRole = Qt.UserRole + 15
AEventPhaseRole = Qt.UserRole + 16
AEventFrequencyRole = Qt.UserRole + 17
AEventOffsetRole = AEventValueRole

# TrackTypes
DigitalTrack = 0
AnalogTrack = 1

# VariableTypes
NumericVariable = 0
CodeVariable = 1

# Playlist item types
Routine = 0
Gap = 1

# Function Types
Constant = 0
Linear = 1
ExpRise = 2
ExpFall = 3
Sine = 4


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


# Check if 'index' is a descendant of 'ancestor'
def is_descendant_of(ancestor : QModelIndex, index: QModelIndex):
    if not index.isValid():
        return False

    if ancestor == index:
        return False

    parent = index.parent()
    while parent.isValid(): # until parent is root element
        if parent == ancestor:
            return True
        parent = parent.parent()

    return False


class SequenceException(Exception):
    pass