
import cards
import json
import utils


class Config:
    def __init__(self):
        with open('config.json') as json_data_file:
            self._data = json.load(json_data_file)
            self._verify()

    def _verify(self):

        # Check that all card names are unique
        card_names = []
        for card in self._data["cards"]:
            if card["name"] in card_names:
                raise utils.SequenceException("Card names must be unique")
            else:
                card_names.append(card["name"])


    def get_cards_dict(self):
        card_dict = {}
        for card in self._data["cards"]:
            class_ = getattr(cards, card["class"])
            card.pop("class")
            card_dict[card["name"]] =  class_(**card)

        return card_dict