
import json
import utils
import hardware
import database

import hardware_specific.dummy
import hardware_specific.buscards
import hardware_specific.artiq

from notify import publisher

class Config:

    def __init__(self, config_path):
        with open(config_path) as json_data_file:
            self.data = json.load(json_data_file)

        self._verify_config()

    def _verify_config(self):
        # Check that all output system names are unique
        outsys_names = []
        for output_system in self.data["output systems"]:
            if output_system["name"] in outsys_names:
                raise utils.SequenceException("Output system names must be unique")
            else:
                outsys_names.append(output_system["name"])

        # Check that all card names are unique
        card_names = []
        for output_system in self.data["output systems"]:
            for card in output_system["cards"]:
                if card["name"] in card_names:
                    raise utils.SequenceException("Card names must be unique")
                else:
                    card_names.append(card["name"])

    def get_hardware(self):
        output_systems_dict = {}

        for output_system_spec in self.data["output systems"]:
            output_system_class = eval(output_system_spec["class"])
            output_systems_dict[output_system_spec["name"]] = output_system_class(output_system_spec)

        return hardware.Hardware(output_systems_dict)

    def get_sequences_path(self):
        return self.data["sequences path"]

    def get_database(self):
        if "database" in self.data:
            if "type" in self.data["database"]:
                if self.data["database"]["type"] == "influxdb2":
                    from databases.influxdb2 import InfluxDB2
                    url = self.data["database"]["url"]
                    token = self.data["database"]["token"]
                    org = self.data["database"]["org"]
                    bucket = self.data["database"]["bucket"]
                    return InfluxDB2(url, token, org, bucket)
            else:
                raise utils.SequenceException("Database section present but no type is defined.")
        return database.Database()

    def get_publisher(self):
        if "notify_server" in self.data:
            if "host" in self.data["notify_server"] and "port" in self.data["notify_server"]:
                host = self.data["notify_server"]["host"]
                port = self.data["notify_server"]["port"]
                print(host, port)
                return publisher.PublisherClient(host, port)
