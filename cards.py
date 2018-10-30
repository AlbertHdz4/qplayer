import utils


class Card:
    num_channels = None
    type = None

    @property
    def channels(self):
        pass

    def parse_card(self):
        pass


class Channel:
    def __init__(self, name, card):
        self.name = name
        self.card = card

    def parse_channel(self):
        return {"name":self.name, "card":self.card.parse_card()}


class BusCard(Card):
    def __init__(self, name, address):
        self.name = name
        self.address = address
        self._channels = []
        for i in range(self.num_channels):
            self._channels.append(Channel(self.name+"-%02d"%i, self))

    @property
    def channels(self):
        return self._channels

    def parse_card(self):
        return {"name": self.name, "address": self.address, "class":self.__class__.__name__}


class DigitalBusCard(BusCard):
    num_channels = 16
    type = utils.DigitalTrack


class AnalogBusCard(BusCard):
    num_channels = 1
    type = utils.AnalogTrack
