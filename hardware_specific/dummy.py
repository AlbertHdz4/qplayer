import utils
from hardware import OutputSystem, Card, Channel

from PyQt5.QtCore import QTimer


class DummyOutputSystem(OutputSystem):
    def __init__(self, system_spec):
        self.name = system_spec["name"]
        self.cards = {}
        self.sequence_end_listeners = []

        for card in system_spec["cards"]:
            card_class = eval(card["class"])
            card_name = card["name"]
            card_address = card["address"]
            card_channels = card["channels"]
            if card_class == DigitalDummyCard:
                self.cards[card_name] = card_class(card_name, card_address, card_channels)
            elif card_class == AnalogDummyCard:
                card_samplerate = card["samplerate"]
                self.cards[card_name] = card_class(card_name, card_address, card_channels, card_samplerate)

    def play_once(self, run_id):
        print("Play dummy %d sequence once"%run_id)
        QTimer.singleShot(1500, self.sequence_finished)

    def stop(self):
        print("Stopped")
        self.timer.stop()
        self.sequence_finished()

class DummyCard(Card):
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


class DigitalDummyCard(DummyCard):
    num_channels = 8
    type = utils.DigitalTrack


class AnalogDummyCard(DummyCard):
    num_channels = 2
    type = utils.AnalogTrack

    def __init__(self, name, address, channels, samplerate):
        super().__init__(name, address, channels)
        self.samplerate = samplerate