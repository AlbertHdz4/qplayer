import utils


class Card:
    num_channels = None
    track_type = None

    @property
    def channels(self):
        pass


class Channel:
    def __init__(self, name):
        self.name = name


class BussCard(Card):
    def __init__(self, name, address):
        self.name = name
        self.address = address
        self._channels = []
        for i in range(self.num_channels):
            self._channels.append(Channel(self.name+"-%02d"%i))

    @property
    def channels(self):
        return self._channels


class DigitalBusCard(BussCard):
    num_channels = 16
    track_type = utils.DigitalTrack


class AnalogBusCard(BussCard):
    num_channels = 1
    track_type = utils.AnalogTrack
