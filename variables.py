#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  variables.py
#  
#

from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel, QAbstractItemModel, QMimeData
from collections import OrderedDict


class VariablesStore:
    def __init__(self):
        self.groups = []

    def appendGroup(self,group):
        self.groups.append(group)
        group.parent = self

    def index(self, group):
        return self.groups.index(group)

    def group(self,row):
        return self.groups[row]

    @property
    def length(self):
        return len(self.groups)



class VariablesGroup:
    def __init__(self, name="",parent=None):
        self.name = name
        self.parent = parent
        self.variables = []

    def addVariable(self, variable):
        self.variables.append(variable)
        variable.parent = self

    def variable(self,row):
        return self.variables[row]

    @property
    def length(self):
        return len(self.variables)

    @property
    def row(self):
        if self.parent:
            return self.parent.index(self)


class Variable:

    columns = 7

    def __init__(self, name, parent=None):
        self.name = name
        self.value = 8
        self.iterating = False
        self.start = 0
        self.stop = 10
        self.step = 1
        self.comment = "[%s]"%name
        self.parent = parent

    @property
    def row(self):
        if self.parent:
            return self.parent.index(self)

    def column(self,col):
        if col == 0:
            return self.name
        elif col == 1:
            return self.value
        elif col == 2:
            return self.comment
        elif col == 3:
            return self.start
        elif col == 4:
            return self.stop
        elif col == 5:
            return self.step
        elif col == 6:
            return self.iterating


    def set_column(self,col,val):
        if col == 0:
            self.name = val
        elif col == 1:
            self.value = val
        elif col == 2:
            self.comment = val
        elif col == 3:
            self.start = val
        elif col == 4:
            self.stop = val
        elif col == 5:
            self.step = val
        elif col == 6:
            self.iterating = val == "true"


class VariablesModel(QAbstractItemModel):
    def __init__(self, data=None, parent=None):
        super(VariablesModel, self).__init__(parent)

        self.rootItem = VariablesStore()

    # Given a row, column, and parent model index this function generates the corresponding model index for the child of
    # the parent in the position row,column. The generated model index contains a pointer to the underlying data.
    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        if isinstance(parentItem, VariablesStore):
            childItem = parentItem.group(row)
        elif isinstance(parentItem, VariablesGroup):
            childItem = parentItem.variable(row)
        else:
            print("Parent is WFT")


        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()



        if isinstance(childItem, VariablesGroup):
            return QModelIndex()
        elif isinstance(childItem, Variable):
            pass
        elif isinstance(childItem, VariablesStore):
            pass

        parentItem = childItem.parent

        return self.createIndex(parentItem.row, 0, parentItem)

    def rowCount(self, parent):
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        if isinstance(parentItem, Variable):
            return 0
        else:
            return parentItem.length

    def columnCount(self, parent):
        return Variable.columns

    def data(self, index: QModelIndex, role):
        pointer = index.internalPointer()
        if role == Qt.DisplayRole:

            if isinstance(pointer,VariablesGroup) and index.column() == 0:
                return pointer.name
            elif isinstance(pointer, Variable):
                col = index.column()
                return pointer.column(col)
        else:
            return None

    def flags(self, index):
        internalPointer = index.internalPointer()

        standard_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsDragEnabled

        if isinstance(internalPointer, VariablesGroup):
            if index.column() > 0:
                return Qt.NoItemFlags
            elif index.column() == 0:
                return standard_flags| Qt.ItemIsDropEnabled

        return standard_flags

    def supportedDropActions(self):
        return Qt.MoveAction

    """
    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex):
        #print(data.text())
        print(data.hasText())
        print(action)
        print(row,column,parent.internalPointer().row)
        print("Drop that!")
        return True
    """

    def moveRows(self, sourceParent: QModelIndex, sourceRow: int, count: int, destinationParent: QModelIndex, destinationChild: int):
        print("Shake it!")
        return True

    def canDropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex):
        return True


    def setData(self, index, value, role):
        if role == Qt.EditRole and len(value) > 0:
            editedItem = index.internalPointer()
            if isinstance(editedItem,VariablesGroup):
                editedItem.name = value
            elif isinstance(editedItem,Variable):
                editedItem.set_column(index.column(),value)
            self.dataChanged.emit(index,index,[Qt.DisplayRole])
        return True

    def addGroup(self, name):
        row = self.rootItem.length
        self.beginInsertRows(QModelIndex(),row,row)
        self.rootItem.appendGroup(VariablesGroup(name))
        self.endInsertRows()

    # add a new variable: name, the new variable name, parent, the row that the variable group occupies
    def addVariable(self, name, parent):
        row = self.rootItem.group(parent).length
        index = self.index(parent,0,QModelIndex())
        self.beginInsertRows(index,row,row)
        self.rootItem.group(parent).addVariable(Variable(name))
        self.endInsertRows()


class StaticVariablesProxyModel(QSortFilterProxyModel):

    def filterAcceptsColumn(self, source_column: int, source_parent: QModelIndex):
        if source_column<2:
            return True
        else:
            return False

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        parentPointer = source_parent.internalPointer()

        if isinstance(parentPointer, VariablesStore):
            return True
        elif isinstance(parentPointer, VariablesGroup):
            return not parentPointer.variable(source_row).iterating
        else:
            return True


class IteratorVariablesProxyModel(QSortFilterProxyModel):

    def filterAcceptsColumn(self, source_column: int, source_parent: QModelIndex):
        if source_column>=2 or source_column==0:
            return True
        else:
            return False

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        parentPointer = source_parent.internalPointer()
        print(type(parentPointer))
        if isinstance(parentPointer, VariablesStore):
            return True
        elif isinstance(parentPointer, VariablesGroup):
            return parentPointer.variable(source_row).iterating
        else:
            return True

