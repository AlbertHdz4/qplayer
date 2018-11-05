import utils


class Card:
    num_channels = None
    type = None

    # TODO: add 'name' as abstract property

    @property
    def channels(self):
        pass

    def get_card_dict(self):
        pass


class Channel:
    def __init__(self, index, name, card):
        self.index = index
        self.name = name
        self.card = card

    def get_channel_dict(self):
        return {"index": self.index, "card": self.card.name}


class BusCard(Card):
    def __init__(self, name, address, channels):
        self.name = name
        self.address = address
        self._channels = []
        for i in range(self.num_channels):
            self._channels.append(Channel(i, channels[i], self))

    @property
    def channels(self):
        return self._channels

    def get_card_dict(self):
        return {"name": self.name, "address": self.address, "class":self.__class__.__name__}


class DigitalBusCard(BusCard):
    num_channels = 8
    type = utils.DigitalTrack


class AnalogBusCard(BusCard):
    num_channels = 2
    type = utils.AnalogTrack
