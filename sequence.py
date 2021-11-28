from variables import VariablesModel
from routines import RoutinesModel
from playlist import PlaylistModel

from PyQt5.QtCore import Qt


class Sequence:

    def __init__(self,variables: VariablesModel, routines: RoutinesModel, playlist: PlaylistModel):
        self.variables = variables
        self.routines = routines
        self.playlist = playlist

    def load_sequence_from_dict(self, sequence):
        self.clear()

        self.variables.load_variables_from_pystruct(sequence["variables"])
        self.routines.load_routines_from_pystruct(sequence["routines"])
        self.playlist.load_playlist_from_pystruct(sequence["playlist"])

    def sequence_to_dict(self):
        variables = self.variables.get_variables_pystruct()
        routines = self.routines.get_routines_pystruct()
        playlist = self.playlist.get_playlist_pystruct()

        sequence = {"variables": variables, "routines": routines, "playlist": playlist}
        return sequence

    def clear(self):
        self.variables.clear()
        self.routines.clear()
        self.playlist.clear()
