from variables import VariablesModel
from routines import RoutinesModel
from playlist import PlaylistModel

from PyQt5.QtCore import Qt

import json

class SequenceManager:

    def __init__(self,variables: VariablesModel, routines: RoutinesModel, playlist: PlaylistModel):
        self.variables = variables
        self.routines = routines
        self.playlist = playlist


    def sequence2json(self):
        pass

    def json2sequence(self):
        pass

    def parse_sequence(self):
        # TODO: move this to variables class
        variables = {}
        for i in range(self.variables.rowCount()):
            group_index = self.variables.index(i,0)
            group_item = self.variables.itemFromIndex(group_index)
            group_name = group_index.data()
            group_variables = []
            for j in range(group_item.rowCount()):
                variable = {}
                for k in range(len(self.variables.variable_fields)):
                    field_name = self.variables.variable_fields[k]
                    if field_name != "iterator":
                        variable[field_name] = group_item.child(j,k).data(Qt.DisplayRole)
                    else:
                        variable[field_name] = (group_item.child(j, k).data(Qt.CheckStateRole) == Qt.Checked)
                group_variables.append(variable)

            variables[group_name] = group_variables

        routines  = {}
        for i in range(self.routines.rowCount()):
            routine_index = self.routines.index(i,0)
            routine_item = self.variables.itemFromIndex(group_index)
            routine_name = routine_index.data()
            print(routine_name)

        sequence = {"variables":variables}
        print(sequence)