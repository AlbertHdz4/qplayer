#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  variables.py
#  
#

from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem


class VariablesModel(QStandardItemModel):
    variable_fields = ["name","value","iterator","start","stop","increment","comment"]
    variable_types = [str, str, bool, float, float, float, str]

    def __init__(self):
        super().__init__()
        self.setHorizontalHeaderLabels(self.variable_fields)

    def add_group(self, name):
        new_item = QStandardItem(name)
        new_row = [new_item]
        for i in range(len(self.variable_fields)-1):
            it = QStandardItem()
            it.setFlags(Qt.NoItemFlags)
            new_row.append(it)
        self.appendRow(new_row)
        self.dataChanged.emit(QModelIndex(),QModelIndex())

    def add_variable(self, parent_idx, **kwargs):
        parent = self.itemFromIndex(parent_idx)
        new_row = []
        for i in range(len(self.variable_fields)):
            field = self.variable_fields[i]
            ftype = self.variable_types[i]
            it = QStandardItem()
            if ftype == bool:
                it.setCheckable(True)

            if kwargs is not None and field in kwargs:
                if ftype == bool and kwargs[field]:
                    it.setCheckState(Qt.Checked)
                else:
                    it.setData(kwargs[field],Qt.DisplayRole)
            new_row.append(it)
        parent.appendRow(new_row)
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def get_group_list(self):
        group_list = []
        for j in range(self.rowCount()):
            group_list.append(self.item(j,0).data(Qt.DisplayRole))
        return group_list


class VariablesProxyModel(QSortFilterProxyModel):
    def __init__(self, accepted_fields, show_static, show_iterator, show_empty_groups):
        super().__init__()
        self.accepted_fields = accepted_fields
        self.show_iterator = show_iterator
        self.show_static = show_static
        self.show_empty_groups = show_empty_groups

    def filterAcceptsColumn(self, source_column: int, source_parent: QModelIndex):
        return VariablesModel.variable_fields[source_column] in self.accepted_fields

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        if source_parent.isValid():  # This is a variable
            row_idx = source_parent.child(source_row,
                                          VariablesModel.variable_fields.index("iterator"))  # Index of interator cell
            if self.sourceModel().data(row_idx, Qt.CheckStateRole) == Qt.Checked:
                return self.show_iterator
            else:
                return self.show_static

        else:  # This is a group
            group_item = self.sourceModel().item(source_row,0) # type: QStandardItem
            visible_contents = 0
            rows = group_item.rowCount()
            col = VariablesModel.variable_fields.index("iterator")
            for j in range(rows):
                print(group_item.child(j, 0).data(Qt.DisplayRole))
                if group_item.child(j,col).data(Qt.CheckStateRole) == Qt.Checked and self.show_iterator:
                    visible_contents += 1
                elif group_item.child(j,col).data(Qt.CheckStateRole) == Qt.Unchecked and self.show_static:
                    visible_contents += 1

            if visible_contents == 0:
                return self.show_empty_groups
            else:
                return True