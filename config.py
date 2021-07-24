
import json
import utils
import hardware

import hardware_specific.dummy
import hardware_specific.buscards
import hardware_specific.artiq


class Config:
    @staticmethod
    def _verify_config(data):

        # Check that all output system names are unique
        outsys_names = []
        for output_system in data["output systems"]:
            if output_system["name"] in outsys_names:
                raise utils.SequenceException("Output system names must be unique")
            else:
                outsys_names.append(output_system["name"])

        # Check that all card names are unique
        card_names = []
        for output_system in data["output systems"]:
            for card in output_system["cards"]:
                if card["name"] in card_names:
                    raise utils.SequenceException("Card names must be unique")
                else:
                    card_names.append(card["name"])

    @staticmethod
    def get_hardware():
        with open('config.json') as json_data_file:
            data = json.load(json_data_file)

        Config._verify_config(data)

        output_systems_dict = {}

        for output_system_spec in data["output systems"]:
            output_system_class = eval(output_system_spec["class"])
            output_systems_dict[output_system_spec["name"]] = output_system_class(output_system_spec)

        return hardware.Hardware(output_systems_dict)
