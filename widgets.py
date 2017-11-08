

from PyQt5.Qt import QStyledItemDelegate, QWidget
from PyQt5.QtWidgets import QStyleOptionViewItem, QTextEdit, QVBoxLayout, QFrame, QPushButton, QLabel
from PyQt5.QtCore import QModelIndex, Qt, QAbstractItemModel, QRegExp
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QMouseEvent
from PyQt5.uic import loadUiType


class TextEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(9)

        editor = QTextEdit(parent)
        editor.setFont(font)
        editor.setTabChangesFocus(True)

        self.highlighter = Highlighter(editor.document())

        return editor

    def setEditorData(self, editor: QTextEdit, index: QModelIndex):
        data = index.model().data(index,Qt.EditRole)
        editor.setPlainText(data)

    def setModelData(self, editor: QTextEdit, model: QAbstractItemModel, index: QModelIndex):
        text = editor.toPlainText()
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

        for i in range(8):
            track = SequenceTrack("DChannel %d"%i, SequenceTrack.digital_track)
            self.layout().addWidget(track)
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            self.layout().addWidget(line)

        for i in range(2):
            track = SequenceTrack("AChannel %d"%i, SequenceTrack.analog_track)
            self.layout().addWidget(track)
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            self.layout().addWidget(line)


class SequenceTrack(QWidget):

    digital_track = 0
    analog_track = 1

    ui_form, ui_base = loadUiType('track-widget.ui')

    def __init__(self, name, track_type):
        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)
        self.ui.track_label.setText(name)
        self.track_type = track_type

    def mouseDoubleClickEvent(self, a0: QMouseEvent):
        if self.track_type == self.digital_track:
            self.ui.track_container.addWidget(DigitalSequenceEvent())
        elif self.track_type == self.analog_track:
            self.ui.track_container.addWidget(AnalogSequenceEvent())

class DigitalSequenceEvent(QWidget):

    ui_form, ui_base = loadUiType('digital-event.ui')

    def __init__(self):
        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)

class AnalogSequenceEvent(QWidget):

    ui_form, ui_base = loadUiType('analog-event.ui')

    def __init__(self):
        super().__init__()
        self.ui = self.ui_form()
        self.ui.setupUi(self)