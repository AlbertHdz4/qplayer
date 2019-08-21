#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  variables.py
#  
#

from PyQt5.QtCore import Qt, QModelIndex, QSortFilterProxyModel, pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
import utils

import numpy as np


class VariablesModel(QStandardItemModel):
    variable_fields = ["name","set", "value","iterator","start","stop","increment","comment"]
    variable_types = [str, str, float, bool, float, float, float, str]

    def __init__(self):
        super().__init__()
        self.setHorizontalHeaderLabels(self.variable_fields)
        self.dataChanged.connect(self.update_values)

    def add_group(self, name):
        new_item = QStandardItem(name)

        font = QFont()
        font.setBold(True)
        font.setFamily('Helvetica')
        new_item.setData(font,Qt.FontRole)

        new_row = [new_item]

        #Add the rest of the columns as inert cells
        for i in range(len(self.variable_fields)-1):
            it = QStandardItem()
            it.setFlags(Qt.NoItemFlags)
            new_row.append(it)
        self.appendRow(new_row)
        self.dataChanged.emit(QModelIndex(),QModelIndex())

        return new_item.index()

    def add_variable(self, parent_idx, **kwargs):
        parent = self.itemFromIndex(parent_idx)
        new_row = []
        for i in range(len(self.variable_fields)):
            field = self.variable_fields[i]
            ftype = self.variable_types[i]
            it = QStandardItem()
            it.setTextAlignment(Qt.AlignTop)
            if ftype == bool:
                it.setCheckable(True)
            if field == "set":
                try:
                    float(kwargs[field]) # If it's numeric value, it can be converted
                    it.setData(utils.NumericVariable, utils.VariableTypeRole)
                except ValueError: # It's not a numeric value, treat as code
                    it.setData(utils.CodeVariable,utils.VariableTypeRole)
                except KeyError: #Field is not defined
                    pass
                except TypeError: # "set" field is None, this occurs for iterating variables
                    pass

            if field == "value":
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)

            if kwargs is not None and field in kwargs:
                if ftype == bool and kwargs[field]:
                    it.setCheckState(Qt.Checked)
                else:
                    it.setData(kwargs[field],Qt.DisplayRole)
            new_row.append(it)
        parent.appendRow(new_row)
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def make_iterating(self, var_idx:QModelIndex):
        self.blockSignals(True)
        self.setData(var_idx, Qt.Checked, Qt.CheckStateRole)
        start_idx = var_idx.parent().child(var_idx.row(),self.variable_fields.index("start"))
        if start_idx.data() == None: #Initialize interator if start is not defined
            value_idx = var_idx.parent().child(var_idx.row(), self.variable_fields.index("value"))
            val = value_idx.data()
            print(val)
            self.setData(start_idx,val)

            stop_idx = var_idx.parent().child(var_idx.row(), self.variable_fields.index("stop"))
            self.setData(stop_idx, val)

            increment_idx = var_idx.parent().child(var_idx.row(), self.variable_fields.index("increment"))
            self.setData(increment_idx, "1")
        self.blockSignals(False)
        self.dataChanged.emit(QModelIndex(), QModelIndex())


    def get_group_list(self):
        group_list = []
        for j in range(self.rowCount()):
            group_list.append(self.item(j,0).data(Qt.DisplayRole))
        return group_list

    def load_variables_from_pystruct(self, variables_dict):
        groups = variables_dict.keys()
        for group in groups:
            group_index = self.add_group(group)
            variables_list = variables_dict[group]
            for variable in variables_list:
                self.add_variable(group_index,**variable)

    # returns the full data of this map in a plain python format for the purpose of saving or processing
    def get_variables_pystruct(self):
        parsed_variables = {}
        for i in range(self.rowCount()):
            group_index = self.index(i,0)
            group_item = self.itemFromIndex(group_index)
            group_name = group_index.data()
            group_variables = []
            for j in range(group_item.rowCount()):
                variable = {}
                for k in range(len(self.variable_fields)):
                    field_name = self.variable_fields[k]
                    if field_name != "iterator":
                        variable[field_name] = group_item.child(j,k).data(Qt.DisplayRole)
                    else:
                        variable[field_name] = (group_item.child(j, k).data(Qt.CheckStateRole) == Qt.Checked)
                group_variables.append(variable)

                parsed_variables[group_name] = group_variables
        return parsed_variables

    # returns a dictionary of all variables and their values. This includes iterating variables.
    def get_variables_dict(self):
        variables = {}
        num_groups = self.rowCount()
        for g in range(num_groups):
            group_index = self.index(g,0)
            num_variables = self.rowCount(group_index)
            for v in range(num_variables):
                var_name = self.index(v, self.variable_fields.index("name"), group_index).data()
                var_value = self.index(v, self.variable_fields.index("value"), group_index).data()
                variables[var_name] = float(var_value)

        return variables

    def get_iterating_variables(self):
        iter_vars = {}
        num_groups = self.rowCount()
        for g in range(num_groups):
            group_index = self.index(g,0)
            print(group_index.data())
            num_variables = self.rowCount(group_index)
            for v in range(num_variables):
                # If it is an interating variable
                if self.index(v,self.variable_fields.index("iterator"),group_index).data(Qt.CheckStateRole) == Qt.Checked:
                    var_name = self.index(v, self.variable_fields.index("name"), group_index).data()
                    var_start = self.index(v, self.variable_fields.index("start"), group_index).data()
                    var_stop = self.index(v, self.variable_fields.index("stop"), group_index).data()
                    var_increment = self.index(v, self.variable_fields.index("increment"), group_index).data()
                    iter_vars[var_name] = {"start":var_start, "stop":var_stop, "increment":var_increment}

        return iter_vars


    def to_number(self, expr, variables=None):
        if variables is None:
            variables = self.get_variables_dict()

        return_value = None
        try:
            return_value = eval(expr,variables)
        except (SyntaxError, ValueError):
            pass

        return return_value

    @pyqtSlot()
    def update_values(self):

        to_do = [] # reference to non-numerical variables
        variables_dict = {'np':np}

        # __builtins__ is added so eval treats 'variables' as we want
        # (it doesn't add the builtin python variables)
        variables_dict["__builtins__"] = {}

        self.blockSignals(True)

        # Loop through all variables to find the numerical ones
        num_groups = self.rowCount()
        for g in range(num_groups):
            # print("g=%d"%g)
            group_index = self.index(g,0)
            num_variables = self.rowCount(group_index)
            # print("num_vars=%d"%num_variables)
            for v in range(num_variables):
                iterator = self.index(v,self.variable_fields.index("iterator"),group_index).data(Qt.CheckStateRole)
                var_name = self.index(v, self.variable_fields.index("name"), group_index).data()

                # Set iterating variables
                if iterator == Qt.Checked:
                    var_start = self.index(v, self.variable_fields.index("start"), group_index).data()
                    val_idx = self.index(v, self.variable_fields.index("value"), group_index)
                    self.setData(val_idx, var_start)
                    variables_dict[var_name] = float(var_start)

                # Set numerical variables
                else:
                    var_set = self.index(v,self.variable_fields.index("set"),group_index).data()
                    if type(var_set) == str:
                        # print("%d %d %s=%s" % (g, v, var_name, var_set))
                        try:
                            var_val = float(var_set)  # Cast variables which are numerical
                            val_idx = self.index(v, self.variable_fields.index("value"), group_index)
                            self.setData(val_idx, "%f"%var_val)
                            variables_dict[var_name] = var_val
                        except ValueError:
                            to_do.append((g,v))

        # Now we do our best to parse code variables
        retry_attempts = 0
        while len(to_do) > 0:
            g, v = to_do.pop()
            group_index = self.index(g, 0)
            var_set = self.index(v, self.variable_fields.index("set"), group_index).data()
            if type(var_set) == str:
                var_set = var_set.replace("return","_return_ =")
                loc_dict = {}
                try:
                    exec(var_set,variables_dict,loc_dict)
                    var_val = loc_dict["_return_"]
                    val_idx = self.index(v, self.variable_fields.index("value"), group_index)
                    var_name_idx = self.index(v, self.variable_fields.index("name"), group_index)
                    self.itemFromIndex(var_name_idx).setBackground(Qt.white)
                    self.itemFromIndex(var_name_idx).setFont(QFont())
                    var_name = var_name_idx.data()
                    self.setData(val_idx, "%f"%var_val)
                    variables_dict[var_name] = var_val
                    retry_attempts = 0
                except NameError:
                    # Return to To-Do list if this doesn't work (if there is no error, it should eventually work once
                    # all the required variables are evaluated)
                    to_do.insert(0,(g,v))
                    retry_attempts += 1
                    if len(to_do) <= retry_attempts:  # Avoid infinite retrys, give up all hope after trying everything
                        print("Error: Variable set cannot be numerically evaluated: %s" % str(to_do))

                        for g,v in to_do:
                            group_index = self.index(g, 0)
                            name_index = self.index(v, self.variable_fields.index("name"), group_index)
                            color = QColor()
                            color.setNamedColor("#ffc5c7")
                            font = QFont()
                            font.setStrikeOut(True)
                            self.itemFromIndex(name_index).setBackground(color)
                            self.itemFromIndex(name_index).setFont(font)
                        break

        self.blockSignals(False)




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
                if group_item.child(j,col).data(Qt.CheckStateRole) == Qt.Checked and self.show_iterator:
                    visible_contents += 1
                elif group_item.child(j,col).data(Qt.CheckStateRole) == Qt.Unchecked and self.show_static:
                    visible_contents += 1

            if visible_contents == 0:
                return self.show_empty_groups
            else:
                return True


    class VariablesException(Exception):
        pass