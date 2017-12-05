from PyQt5.QtCore import Qt
from PyQt5.QtGui import QValidator

# User-defined role to use with QStandardItemModel
TrackTypeRole = Qt.UserRole+1
ChannelRole = Qt.UserRole+2
VariableTypeRole = Qt.UserRole+3
EventStartRole = Qt.UserRole+4
EventDurationRole = Qt.DisplayRole
TrackOffsetRole = Qt.UserRole+6

#TrackTypes
DigitalTrack = 0
AnalogTrack = 1

#VariableTypes
NumericVariable = 0
CodeVariable = 1


