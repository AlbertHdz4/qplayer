class Hardware:
    def __init__(self, output_systems):
        self.output_systems = output_systems
        self.sequence_end_listeners = []
        self.output_system_running = {}
        for outsys_name in self.output_systems:
            self.output_system_running[outsys_name] = False
            self.output_systems[outsys_name].add_sequence_end_listener(self.output_system_sequence_finished)

    def get_cards(self):
        cards = {}
        for outsys in self.output_systems:
            cards.update(self.output_systems[outsys].get_cards())
        return cards

    def process_sequence(self, sequence):
        # TODO: separate the sequence by the cards corresponding to each output system and forward the request.
        pass

    def play_once(self):
        for outsys_name in self.output_systems:
            outsys = self.output_systems[outsys_name]
            outsys.play_once()
            self.output_system_running[outsys_name] = True

    def play(self):
        for outsys_name in self.output_systems:
            outsys = self.output_systems[outsys_name]
            outsys.play()
            self.output_system_running[outsys_name] = True

    def stop(self):
        for outsys_name in self.output_systems:
            outsys = self.output_systems[outsys_name]
            outsys.stop()

    def add_sequence_end_listener(self, callback):
        self.sequence_end_listeners.append(callback)

    # This sequence_finished signal is called when ALL of the output systems have finished
    def sequence_finished(self):
        print("Sequence finished")
        for callback in self.sequence_end_listeners:
            callback()

    def output_system_sequence_finished(self, output_system_name):
        self.output_system_running[output_system_name] = False
        if all(value is False for value in self.output_system_running.values()):
            self.sequence_finished()


class OutputSystem:
    def __init__(self, system_spec):
        self.name = None # Must be populated by subclasses
        self.cards = {} # must be filled by subclasses with instances of Card
        self.sequence_end_listeners = []

    def get_cards(self):
        return self.cards

    # Process the sequence and send it to the hardware
    def set_sequence(self, sequence):
        pass

    # Triggers the reproduction of the sequence. set_sequence must be called before.
    def play_once(self):
        pass

    # Triggers the reproduction of the sequence. set_sequence must be called before.
    def play(self):
        pass

    def stop(self):
        pass

    # This method should be called by the subclass when the reproduction of the sequence ends.
    def sequence_finished(self):
        print("Sequence finished from "+self.name)
        for callback in self.sequence_end_listeners:
            callback(self.name)

    # TODO: is there a more QT way of doing this with signals/slots ?
    def add_sequence_end_listener(self, callback):
        self.sequence_end_listeners.append(callback)


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