import utils
from hardware import OutputSystem, Card, Channel
import numpy as np

from PyQt5.QtCore import QTimer

import sipyco.pc_rpc as rpc


class ARTIQOutputSystem(OutputSystem):
    def __init__(self, system_spec):
        self.name = system_spec["name"]
        self.cards = {}
        self.sequence_end_listeners = []
        self.master_host = system_spec["master_host"]
        self.master_port = system_spec["master_port"]
        self.experiment_file_path = system_spec["experiment_file_path"]
        self.master_scheduler = rpc.Client(self.master_host, self.master_port, "master_schedule")
        self.master_experiment_db = rpc.Client(self.master_host, self.master_port, "master_experiment_db")

        with open('hardware_specific/artiq/experiment_template.py', 'r') as f:
            self.experiment_template = f.read()

        for card in system_spec["cards"]:
            card_class = eval(card["class"])
            card_name = card["name"]
            card_channels = card["channels"]
            if card_class == TTLOutARTIQCard:
                self.cards[card_name] = card_class(card_name, card_channels)
            elif card_class == ZotinoARTIQCard:
                card_samplerate = card["samplerate"]
                self.cards[card_name] = card_class(card_name, card_channels, card_samplerate)

    # Process the sequence and send it to the hardware
    def process_sequence(self, sequence, run_id):

        # Convert analog sequences to actual values for the DAC
        for chan in sequence:
            if sequence[chan]['chan'].card.type == utils.DigitalTrack:
                pass # nothing to do
            elif sequence[chan]['chan'].card.type == utils.AnalogTrack:
                samplerate = sequence[chan]['chan'].card.samplerate
                exploded_events = []
                events = sequence[chan]["events"]
                for event in events:
                    if event['type'] == 'constant':
                        new_event = {'duration':event['duration'],
                                     'value':   event['value'],
                                     'time':    event['time']}
                        exploded_events.append(new_event)

                    elif event['type'] == 'linear':
                        start_val = event['start_val']
                        end_val = event['end_val']
                        duration = event['duration']
                        t0 = event['time']
                        num_points = int(duration*samplerate*1e-3)+1 #convert samplerate to 1/ms
                        t = np.linspace(t0, duration+t0, num_points)
                        dt = t[1]-t[0]
                        v = np.linspace(start_val, end_val, num_points)
                        for i in range(num_points-1):
                            new_event = {'duration': dt,
                                         'value': v[i],
                                         'time': t[i]}
                            exploded_events.append(new_event)

                        # TODO: figure out what to do with zero-legth events

                        new_event = {'duration': 0,
                                     'value': v[-1],
                                     'time': t[-1]}
                        exploded_events.append(new_event)


                    elif event['type'] == 'sin':
                        pass
                    elif event['type'] == 'exp':
                        pass

                sequence[chan]["events"] = exploded_events

        # an event dictionary where key is the time of the event.
        # the channel is added to the event so that the sequence can be created
        all_events = {}
        for chan in sequence:
            for event in sequence[chan]['events']:
                event['chan_id'] = chan
                event['chan'] = sequence[chan]['chan']
                t = event['time']
                if t in all_events:
                    all_events[t].append(event)
                else:
                    all_events[t] = [event]

        # write experiment file
        exp_str = self.create_experiment_str(all_events, run_id)
        with open(self.experiment_file_path%run_id, 'w') as f:
            f.write(exp_str)

        self.master_experiment_db.scan_repository()

    def create_experiment_str(self, all_events, run_id):
        times = list(all_events.keys())
        times.sort()

        experiment = ""

        tprev = 0
        for t in times:
            experiment += " "*8 + "delay(%f*ms)\n" % (t - tprev)
            events = all_events[t]
            for event in events:
                # TODO: cleanup by moving each code generation part to the corresponding card
                event_str = ""
                if event['chan'].card.type == utils.DigitalTrack:
                    if event['state'] == 1:
                        event_str = "        self.%s%d.on()"%(event['chan_id'][0], event['chan_id'][1])
                    elif event['state'] == 0:
                        event_str = "        self.%s%d.off()" % (event['chan_id'][0], event['chan_id'][1])

                elif event['chan'].card.type == utils.AnalogTrack:
                    event_str += "        self.%s.write_dac(%d, %f)\n" % (event['chan_id'][0], event['chan_id'][1], event['value'])
                    event_str += "        self.%s.load()" % (event['chan_id'][0])
                    # TODO: subtract from the following delay the time for write_dac and load

                experiment += event_str + "\n"
            tprev = t

        return self.experiment_template.replace("{{id}}", "%d"%run_id).replace("{{experiment}}", experiment)

    def play_once(self, run_id):
        expid = {
            "class_name": "PyPlayerGeneratedExperiment%d" % run_id,
            "file": "pyplayer_%d.py" % run_id,
            "arguments": {"arg_name": 5},
            "log_level": 10,
            "repo_rev": "N/A",
        }

        self.master_scheduler.submit(pipeline_name="main", expid=expid, priority=0, due_date=None, flush=False)
        print("Play artiq sequence once")
        QTimer.singleShot(1500, self.sequence_finished)

    def play(self):
        print("Play artiq sequence")
        self.timer = QTimer()
        self.timer.timeout.connect(self.sequence_finished)
        self.timer.start(1500)

    def stop(self):
        print("Stopped")
        self.timer.stop()
        self.sequence_finished()

class ARTIQCard(Card):
    def __init__(self, name, channels):
        self.name = name
        self._channels = []
        for i in range(self.num_channels):
            self._channels.append(Channel(i, channels[i], self))

    @property
    def channels(self):
        return self._channels

    def get_card_dict(self):
        return {"name": self.name, "class":self.__class__.__name__}


class TTLOutARTIQCard(ARTIQCard):
    num_channels = 16
    type = utils.DigitalTrack


class ZotinoARTIQCard(ARTIQCard):
    num_channels = 32
    type = utils.AnalogTrack

    def __init__(self, name, channels, samplerate):
        super().__init__(name, channels)
        self.samplerate = samplerate