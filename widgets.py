

from PyQt5.Qt import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
import utils
from routines import RoutinesModel


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
            #editor.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)

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

    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(2)
        self.layout().setAlignment(Qt.AlignTop)
        self.model = None # type: QStandardItemModel
        self.tracks = []

    def add_track(self,track_name, channel):
        track = SequenceTrack(track_name, channel)
        self.layout().addWidget(track)
        # line = QFrame()
        # line.setFrameShape(QFrame.HLine)
        # line.setFrameShadow(QFrame.Sunken)
        # self.layout().addWidget(line)

    def clear(self):
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)

    def set_model(self,model: QStandardItemModel):
        self.model = model
        self.model.dataChanged.connect(self.data_changed)

    def set_routine(self, index: int):
        root_index = self.model.index(index,0) # type: QModelIndex
        routine_item = self.model.itemFromIndex(root_index)


        self.clear()

        for i in range(routine_item.rowCount()):
            track_item = routine_item.child(i)
            channel = track_item.data(utils.ChannelRole)
            self.add_track(track_item.data(Qt.DisplayRole), channel)

            #for j in range(track_item.rowCount()):
            #    event_item = track_item.child(j)
            #    self.tracks[i].add_event(event_item.data(Qt.DisplayRole))



    @pyqtSlot()
    def data_changed(self):
        print("routine model data changed")


class SequenceTrack(QWidget):
    ui_form, ui_base = loadUiType('track-widget.ui')

    def __init__(self, name, channel):
        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)
        self.ui.track_label.setText(name)
        self.channel = channel

    def mouseDoubleClickEvent(self, a0: QMouseEvent):
        if self.channel.card.type == utils.DigitalTrack:
            self.ui.track_container.addWidget(DigitalSequenceEvent())
        elif self.channel.card.type == utils.AnalogTrack:
            self.ui.track_container.addWidget(AnalogSequenceEvent())

    def add_event(self,duration):
        self.ui.track_container.addWidget(DigitalSequenceEvent(duration))

class DigitalSequenceEvent(QWidget):

    ui_form, ui_base = loadUiType('digital-event.ui')

    def __init__(self, duration=""):
        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)
        self.ui.event_duration.setText(duration)


class AnalogSequenceEvent(QWidget):

    ui_form, ui_base = loadUiType('analog-event.ui')

    def __init__(self):
        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)


class RoutinePropertiesDialog(QDialog):
    ui_form, ui_base = loadUiType('routine-properties.ui')

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
        if index is not None:
            num_channles = self.model.rowCount(index)

            self.ui.routine_name.setText(index.data(Qt.DisplayRole))

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

