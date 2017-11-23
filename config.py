
import cards
import json


class Config:
    def __init__(self):
        with open('config.json') as json_data_file:
            self._data = json.load(json_data_file)

    def get_cards(self):
        card_list = []
        for card in self._data["cards"]:
            class_ = getattr(cards, card["class"])
            card.pop("class")
            card_list.append(class_(**card))

        return card_list