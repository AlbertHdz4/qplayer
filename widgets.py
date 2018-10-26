

from PyQt5.Qt import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
import utils
import cards
from routines import RoutinesModel
from playlist import PlaylistModel, PlaylistMoveRoutineProxyModel

# This class was created so that code variables have syntax highlighting
class VariableEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        variable_type = index.data(utils.VariableTypeRole)
        if variable_type == utils.CodeVariable:

            font = QFont()
            font.setFamily('Courier')
            font.setFixedPitch(True)
            font.setPointSize(9)

            editor = QTextEdit(parent)
            editor.setFont(font)
            editor.setTabChangesFocus(True)
            editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

            self.highlighter = Highlighter(editor.document())

            return editor

        else:
            editor = QLineEdit(parent)
            editor.setValidator(QDoubleValidator())
            return editor

    def setEditorData(self, editor, index: QModelIndex):
        variable_type = index.data(utils.VariableTypeRole)
        data = index.model().data(index, Qt.EditRole)
        if variable_type == utils.CodeVariable:
            editor.setPlainText(data)
        else:
            editor.setText(data)

    def setModelData(self, editor, model: QAbstractItemModel, index: QModelIndex):
        variable_type = index.data(utils.VariableTypeRole)
        if variable_type == utils.CodeVariable:
            text = editor.toPlainText()
        else:
            text = editor.text()
        model.setData(index, text, Qt.EditRole)

    def updateEditorGeometry(self, editor: QTextEdit, option: QStyleOptionViewItem, index: QModelIndex):
        editor.setGeometry(option.rect)


# source https://github.com/baoboa/pyqt5/blob/master/examples/richtext/syntaxhighlighter.py
class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(Qt.darkBlue)
        keywordFormat.setFontWeight(QFont.Bold)

        keywordPatterns = ["\\bfor\\b", "\\bclass\\b", "\\bin\\b", "\\breturn\\b",
                           "\\bnot\\b", "\\bdef\\b", "\\blambda\\b"]

        self.highlightingRules = [(QRegExp(pattern), keywordFormat)
                for pattern in keywordPatterns]

        classFormat = QTextCharFormat()
        classFormat.setFontWeight(QFont.Bold)
        classFormat.setForeground(Qt.darkMagenta)
        self.highlightingRules.append((QRegExp("\\bQ[A-Za-z]+\\b"),
                classFormat))

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(Qt.red)
        self.highlightingRules.append((QRegExp("#[^\n]*"), singleLineCommentFormat))

        self.multiLineCommentFormat = QTextCharFormat()
        self.multiLineCommentFormat.setForeground(Qt.red)

        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(Qt.darkGreen)
        self.highlightingRules.append((QRegExp("\".*\""), quotationFormat))
        self.highlightingRules.append((QRegExp("'.*'"), quotationFormat))

        functionFormat = QTextCharFormat()
        functionFormat.setFontItalic(True)
        functionFormat.setForeground(Qt.blue)
        self.highlightingRules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\()"), functionFormat))

        self.commentStartExpression = QRegExp("/\\*")
        self.commentEndExpression = QRegExp("\\*/")

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()

            self.setFormat(startIndex, commentLength, self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.indexIn(text, startIndex + commentLength)


class SequenceEditor(QWidget):

    def __init__(self, model):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setAlignment(Qt.AlignTop)
        self.model = model # type: QStandardItemModel

        self.model.dataChanged.connect(self.data_changed)

        self.routine_row = None

    def add_channel_widget(self, row, track_name, channel: cards.Channel):
        track = SequenceChannel(row, track_name, channel, self)
        self.layout().addWidget(track)

    # Remove all widgets: this is used when the sequence editor is loaded with a new routine so the old one must go
    def clear(self):
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget() # type: QWidget
            widget.setParent(None)
            widget.destroy()

    def get_current_routine_item(self):
        if self.routine_row is not None:
            return self.model.item(self.routine_row, 0)
        return None

    def set_routine(self, routine_row: int):
        self.routine_row = routine_row
        root_index = self.model.index(self.routine_row,0) # type: QModelIndex
        routine_item = self.model.itemFromIndex(root_index)

        self.clear()

        for i in range(routine_item.rowCount()):
            channel_item = routine_item.child(i)
            channel = channel_item.data(utils.ChannelRole) # type: cards.Channel
            self.add_channel_widget(i, channel_item.data(Qt.DisplayRole), channel)

            for j in range(channel_item.rowCount()):
                event_item = channel_item.child(j)
                self.layout().itemAt(i).widget().add_event(event_item)


        self.model.dataChanged.emit(QModelIndex(), QModelIndex()) # send data changed notification to everything to set up new gui elements



    @pyqtSlot()
    def data_changed(self):
        pass
        # print("routine model data changed")


class SequenceChannel(QWidget):
    ui_form, ui_base = loadUiType('track-widget.ui')

    def __init__(self, row, name, channel, sequence_editor):
        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)
        self.ui.track_label.setText(name)
        self.channel = channel
        self.row = row
        self.sequence_editor = sequence_editor # type: SequenceEditor
        self.ui.track_offset.editingFinished.connect(self.offset_edited)
        self.sequence_editor.model.dataChanged.connect(self.data_changed)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.add_event()

    def get_model_item(self):
        current_routine_index = self.sequence_editor.get_current_routine_item() # type: QStandardItem
        return current_routine_index.child(self.row)

    # if event_item is None, a new item will be added to the model
    # event_item will be None if the event was added through a dobule click of the empty track
    def add_event(self, event_item=None):
        if self.channel.card.type == utils.DigitalTrack:
            self.ui.track_container.addWidget(DigitalSequenceEvent(self,event_item))
        elif self.channel.card.type == utils.AnalogTrack:
            self.ui.track_container.addWidget(AnalogSequenceEvent(self,event_item))

    def position_of_event(self, sequence_event):
        return self.ui.track_container.indexOf(sequence_event)

    # def row(self):
    #     return self.sequence_editor.layout().indexOf(self)

    @pyqtSlot()
    def offset_edited(self):
        self.get_model_item().setData(self.ui.track_offset.text(), utils.TrackOffsetRole)

    @pyqtSlot()
    def data_changed(self):
        # Update offset
        if self.get_model_item() is not None:
            self.ui.track_offset.setText(self.get_model_item().data(utils.TrackOffsetRole))


class SequenceEvent(QWidget):

    ui_file = None

    def __init__(self, sequence_track, event_item):
        super().__init__()

        self.sequence_track = sequence_track # type: SequenceChannel
        self.event_item = event_item

        if self.event_item is None:
            self.event_item = QStandardItem()
            self.sequence_track.get_model_item().appendRow(self.event_item)
            self.initialize_event_item(self.event_item) # we init after append so that the item has a reference to the model

        self.event_item.model().dataChanged.connect(self.data_changed)

        self.ui_form, self.ui_base = loadUiType(self.ui_file)
        self.ui = self.ui_form()
        self.ui.setupUi(self)

        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.customContextMenuRequested.connect(self.context_menu_requested)

        self.event_item.emitDataChanged()

    def initialize_event_item(self, event_item):
        pass

    @pyqtSlot()
    def data_changed(self):
        pass

    @pyqtSlot(QPoint)
    def context_menu_requested(self,pos):
        menu = QMenu()
        delete_event_action = menu.addAction("Delete event")
        move_right_action = menu.addAction("Move right")
        move_left_action = menu.addAction("Move left")
        action = menu.exec(self.mapToGlobal(pos))  # type: QMenu

        if action == delete_event_action:
            self.delete()
        elif action == move_right_action:
            # TODO: move events
            print("Not implemented!")
        elif action == move_left_action:
            # TODO: move events
            print("Not implemented!")

    def mouseDoubleClickEvent(self, event: QEvent):
        print(self.sequence_track.position_of_event(self))

    def delete(self):
        self.event_item.model().removeRow(self.event_item.row(),self.event_item.parent().index())
        self.setParent(None)


class DigitalSequenceEvent(SequenceEvent):
    ui_file = "digital-event.ui"

    def __init__(self, sequence_track, event_item):
        super().__init__(sequence_track, event_item)
        self.ui.state_button.toggled.connect(self.toggled)
        self.ui.event_duration.editingFinished.connect(self.duration_edited)

    # Initialize the event item in the model
    def initialize_event_item(self, event_item: QStandardItem):
        event_item.model().init_digital_event_item(event_item)

    @pyqtSlot()
    def data_changed(self):
        # Update button state
        self.ui.state_button.setChecked(self.event_item.checkState())

        # Update duration
        self.ui.event_duration.setText(self.event_item.data(utils.EventDurationRole))
        brush = self.event_item.background() # type: QBrush
        self.ui.event_duration.setStyleSheet("QLineEdit { background: "+brush.color().name()+" }")

        # Update start label
        self.ui.start_label.setText("start: %0.3f"%(self.event_item.data(utils.EventStartRole)))

    @pyqtSlot(bool)
    def toggled(self, checked):
        if checked:
            self.event_item.setCheckState(Qt.Checked)
        else:
            self.event_item.setCheckState(Qt.Unchecked)

    @pyqtSlot()
    def duration_edited(self):
        self.event_item.setData(self.ui.event_duration.text(), utils.EventDurationRole)


class AnalogSequenceEvent(SequenceEvent):
    ui_file = "analog-event.ui"

    def initialize_event_item(self, event_item: QStandardItem):
        event_item.model().init_analog_event_item(event_item)


class RoutinePropertiesDialog(QDialog):
    ui_form, ui_base = loadUiType('routine-properties-dialog.ui')

    def __init__(self, cards, model: RoutinesModel, index: QModelIndex=None):
        self.model = model

        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)

        self.ui.all_button.clicked.connect(self.selectAll)
        self.ui.none_button.clicked.connect(self.selectNone)
        self.ui.button_box.accepted.connect(self.submitted)

        channel_list = self.ui.channel_list  # type: QListWidget

        active_channels  = []
        self.old_name = None

        if index is not None:
            num_channles = self.model.rowCount(index)

            self.old_name = index.data(Qt.DisplayRole)
            self.ui.routine_name.setText(self.old_name)

            for r in range(num_channles):
                chan_index = model.index(r,0,index)
                chan = chan_index.data(utils.ChannelRole)
                print(chan.name)
                active_channels.append(chan)

        for card in cards:
            for chan in card.channels:
                new_item = QListWidgetItem(chan.name)
                new_item.setData(utils.ChannelRole,chan)
                new_item.setFlags(new_item.flags() | Qt.ItemIsUserCheckable )
                if chan in active_channels:
                    new_item.setCheckState(Qt.Checked)
                else:
                    new_item.setCheckState(Qt.Unchecked)
                channel_list.addItem(new_item)


    @pyqtSlot()
    def selectAll(self):
        channel_list = self.ui.channel_list  # type: QListWidget
        for i in range(channel_list.count()):
            channel_list.item(i).setCheckState(Qt.Checked)

    @pyqtSlot()
    def selectNone(self):
        channel_list = self.ui.channel_list  # type: QListWidget
        for i in range(channel_list.count()):
            channel_list.item(i).setCheckState(Qt.Unchecked)

    @pyqtSlot()
    def submitted(self):
        existing_routine_names = self.model.get_routine_names()
        try:
            existing_routine_names.remove(self.old_name)
        except ValueError:
            pass

        if len(self.name) == 0:
            message_box = QMessageBox(self)
            message_box.setText("Routine name must not be empty.");
            message_box.exec()
        elif self.name in existing_routine_names:
            message_box = QMessageBox(self)
            message_box.setText("Routine name must be unique.");
            message_box.exec()
        else:
            self.accept()

    @property
    def name(self):
        return self.ui.routine_name.text()

    @property
    def active_channels(self):

        channel_list = self.ui.channel_list  # type: QListWidget

        active_channels_ = []

        for i in range(channel_list.count()):
            item = channel_list.item(i) # type: QListWidgetItem
            if item.checkState() == Qt.Checked:
                active_channels_.append(item.data(utils.ChannelRole))

        return active_channels_


class MoveRoutineDialog(QDialog):
    ui_form, ui_base = loadUiType('move-routine-dialog.ui')

    def __init__(self, playlist_model: PlaylistModel, index: QModelIndex=None):
        self.playlist_model = playlist_model
        self.index_to_move = index
        self.model = PlaylistMoveRoutineProxyModel(index)
        self.model.setSourceModel(self.playlist_model)

        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)

        self.ui.button_box.accepted.connect(self.submitted)

        self.ui.tree_view.setModel(self.model)
        self.ui.tree_view.expandAll()

    @pyqtSlot()
    def submitted(self):
        new_parent_index = self.model.mapToSource(self.ui.tree_view.currentIndex()) # type: QModelIndex
        self.playlist_model.move_branch(self.index_to_move,new_parent_index)

        self.accept()

class UniqueTextInputDialog(QDialog):
    ui_form, ui_base = loadUiType('text-input-dialog.ui')

    def __init__(self, text_label, existing_values, initial_text = ""):
        self.existing_values = existing_values

        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)


        self.ui.button_box.accepted.connect(self.submitted)
        self.ui.text_label.setText(text_label)
        self.ui.text_line_edit.setText(initial_text)

    @property
    def name(self):
        return self.ui.text_line_edit.text()

    @pyqtSlot()
    def submitted(self):
        if len(self.name) == 0:
            message_box = QMessageBox(self)
            message_box.setText("Name must not be empty.");
            message_box.exec()
        elif self.name in self.existing_values:
            message_box = QMessageBox(self)
            message_box.setText("Name must be unique.");
            message_box.exec()
        else:
            self.accept()