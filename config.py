
import cards
import json


class Config:
    def __init__(self):
        with open('config.json') as json_data_file:
            self._data = json.load(json_data_file)

    def get_cards_dict(self):
        card_dict = {}
        for card in self._data["cards"]:
            class_ = getattr(cards, card["class"])
            card.pop("class")
            card_dict[card["name"]] =  class_(**card)

        return card_dict