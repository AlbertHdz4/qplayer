

from PyQt5.Qt import QStyledItemDelegate, QWidget
from PyQt5.QtWidgets import QStyleOptionViewItem, QTextEdit
from PyQt5.QtCore import QModelIndex, Qt, QAbstractItemModel, QRegExp
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont


class TextEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(9)

        editor = QTextEdit(parent)
        editor.setFont(font)

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
        self.highlightingRules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\()"),
                functionFormat))

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

            self.setFormat(startIndex, commentLength,
                    self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.indexIn(text,
                    startIndex + commentLength);