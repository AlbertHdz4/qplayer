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
        variables = self.variables.get_parsed_variables()
        routines = self.routines.get_parsed_routines()
        playlist = self.playlist.get_parsed_playlist()

        sequence = {"variables":variables, "routines": routines, "playlist": playlist}
        print("variables")
        print(variables)
        print("routines")
        print(routines)
        print("playlist")
        print(playlist)

        return sequence