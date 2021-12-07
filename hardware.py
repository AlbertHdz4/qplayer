# The Hardware class is basically a way to control a collection of OutputSystems which are the
# abstraction of a specific piece of hardware that will output a sequence.

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

    # This function is called before play_once/play
    def process_sequence(self, sequence, run_id):
        # separate the sequence by the cards corresponding to each output system and forward the request.
        for outsys in self.output_systems:

            outsys_sequence = {}
            cards = self.output_systems[outsys].get_cards().keys()

            for chan in sequence:
                if chan[0] in cards:
                    outsys_sequence[chan] = sequence[chan]

            self.output_systems[outsys].process_sequence(outsys_sequence, run_id)

    def cycle_init(self):
        for outsys_name in self.output_systems:
            outsys = self.output_systems[outsys_name]
            outsys.cycle_init()

    def play_once(self, run_id):
        for outsys_name in self.output_systems:
            outsys = self.output_systems[outsys_name]
            outsys.play_once(run_id)
            self.output_system_running[outsys_name] = True

    def stop(self):
        for outsys_name in self.output_systems:
            outsys = self.output_systems[outsys_name]
            outsys.stop()

    def add_sequence_end_listener(self, callback):
        self.sequence_end_listeners.append(callback)

    # This sequence_finished signal is called when ALL of the output systems  are ready to receive a new sequence
    def sequence_finished(self):
        print("hardware: Sequence finished")
        for callback in self.sequence_end_listeners:
            callback()

    def output_system_sequence_finished(self, output_system_name):
        self.output_system_running[output_system_name] = False
        if all(value is False for value in self.output_system_running.values()):
            self.sequence_finished()


class OutputSystem:
    # initialize OutputSystem
    # `system_spec` is the part of the configuration related to this output system
    def __init__(self, system_spec):
        self.name = None # Must be populated by subclasses
        self.cards = {} # must be filled by subclasses with instances of Card
        self.sequence_end_listeners = []

    def get_cards(self):
        return self.cards

    # Process the sequence and send it to the hardware
    def process_sequence(self, sequence, run_id):
        pass

    # Cycle initialization, this is called before a sequence or set of sequences is executed to prepare the hardware
    def cycle_init(self):
        pass

    # Triggers the reproduction of the sequence. set_sequence must be called before.
    def play_once(self, run_id):
        pass

    def stop(self):
        pass

    # This method should be called by the subclass when the OutputSystem is ready to receive a new sequence.
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