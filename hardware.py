class Hardware:
    def __init__(self, output_systems):
        self.output_systems = output_systems

    def get_cards(self):
        cards = {}
        for outsys in self.output_systems:
            cards.update(self.output_systems[outsys].get_cards())
        return cards


class OutputSystem:
    def __init__(self, **kwargs):
        self.name = None # Must be populated by subclasses
        self.cards = [] # must be filled by subclasses with instances of Card
        pass

    def get_cards(self):
        return self.cards


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