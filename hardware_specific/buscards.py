import utils
from hardware import OutputSystem, Card, Channel


class BuscardsOutputSystem(OutputSystem):
    def __init__(self, system_spec):
        self.name = system_spec["name"]
        self.cards = {}

        for card in system_spec["cards"]:
            card_class = eval(card["class"])
            card_name = card["name"]
            card_address = card["address"]
            card_channels = card["channels"]
            if card_class == DigitalBusCard:
                self.cards[card_name] = card_class(card_name, card_address, card_channels)
            elif card_class == AnalogBusCard:
                card_samplerate = card["samplerate"]
                self.cards[card_name] = card_class(card_name, card_address, card_channels, card_samplerate)


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

    def __init__(self, name, address, channels, samplerate):
        super(AnalogBusCard, self).__init__(name, address, channels)
        self.samplerate = samplerate