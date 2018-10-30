from variables import VariablesModel
from routines import RoutinesModel
from playlist import PlaylistModel

from PyQt5.QtCore import Qt

class SequenceManager:

    def __init__(self,variables: VariablesModel, routines: RoutinesModel, playlist: PlaylistModel):
        self.variables = variables
        self.routines = routines
        self.playlist = playlist

    def load_sequence(self,sequence):
        self.variables.load_parsed_variables(sequence["variables"])
        self.routines.load_parsed_routines(sequence["routines"])
        self.playlist.load_parsed_playlist(sequence["playlist"])

    def parse_sequence(self):
        variables = self.variables.get_parsed_variables()
        routines = self.routines.get_parsed_routines()
        playlist = self.playlist.get_parsed_playlist()

        sequence = {"variables": variables, "routines": routines, "playlist": playlist}
        return sequence