import utils
from hardware import OutputSystem, Card, Channel
import numpy as np

from sipyco.pc_rpc import Client
from sipyco.sync_struct import Subscriber
import asyncio
import os


def voltage_to_mu(voltage):
    # Copied from artiq source code
    vref = 5
    offset_dacs = 8192
    code = int(round((1 << 16) * (voltage / (4. * vref)) + offset_dacs * 0x4))
    if code < 0x0 or code > 0xffff:
        raise ValueError("Invalid DAC voltage!")
    return code


def seconds_to_mu(seconds):
    # Copied from artiq source code
    ref_period = 1e-9
    return np.int64(seconds // ref_period)


class ARTIQOutputSystem(OutputSystem):
    def __init__(self, system_spec):
        self.name = system_spec["name"]
        self.cards = {}
        self.sequence_end_listeners = []
        self.master_host = system_spec["master_host"]
        self.master_control_port = system_spec["master_control_port"]
        self.master_notify_port = system_spec["master_notify_port"]
        self.master_scheduler = Client(self.master_host, self.master_control_port, "master_schedule")
        self.master_experiment_db = Client(self.master_host, self.master_control_port, "master_experiment_db")
        self.schedule_subscriber = Subscriber("schedule",
                                              target_builder=self.artiq_schedule_setup,
                                              notify_cb=self.artiq_schedule_update)
        self.experiment_schedule = {}
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.schedule_subscriber.connect(self.master_host, self.master_notify_port))

        self.exp_str = None
        self.last_delay = 0
        self.initializing = False

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

        sequence_duration = 0
        # Convert analog sequences to actual values for the DAC and calculate sequence duration
        for chan in sequence:
            track_duration = 0
            for event in sequence[chan]["events"]:
                track_duration += event['duration']
            sequence_duration = max(sequence_duration, track_duration)

            if sequence[chan]['chan'].card.type == utils.DigitalTrack:
                pass
            elif sequence[chan]['chan'].card.type == utils.AnalogTrack:
                samplerate = sequence[chan]['chan'].card.samplerate
                exploded_events = []
                events = sequence[chan]["events"]
                for event in events:
                    if event['type'] == 'constant':
                        new_event = {'duration': event['duration'],
                                     'value': event['value'],
                                     'time': event['time']}
                        exploded_events.append(new_event)

                    elif event['type'] == 'linear':
                        start_val = event['start_val']
                        end_val = event['end_val']
                        duration = event['duration']
                        t0 = event['time']
                        num_points = int(duration * samplerate * 1e-3) + 1  # convert samplerate to 1/ms
                        t = np.linspace(t0, duration + t0, num_points)
                        dt = t[1] - t[0]
                        v = np.linspace(start_val, end_val, num_points)
                        for i in range(num_points - 1):
                            new_event = {'duration': dt,
                                         'value': v[i],
                                         'time': t[i]}
                            exploded_events.append(new_event)

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

        self.exp_str = self.create_experiment_str(all_events)
        last_t = max(all_events.keys())
        self.last_delay = str(seconds_to_mu((sequence_duration-last_t)*1e-3))

    def create_experiment_str(self, all_events):
        times = list(all_events.keys())
        times.sort()

        experiment_str = ""

        for t in times:
            events = all_events[t]
            time_events_str = ""
            for event in events:
                # TODO: cleanup by moving each code generation part to the corresponding card
                event_str = ""
                if event['chan'].card.type == utils.DigitalTrack:
                    event_str = "(0,%d,%d)" % (event['chan_id'][1], event['state'])

                elif event['chan'].card.type == utils.AnalogTrack:
                    # TODO: subtract from the following delay the time for write_dac and load
                    event_str = "(1,%d,%d)" % (event['chan_id'][1], voltage_to_mu(event['value']))

                time_events_str += event_str+','

            time_events_str = time_events_str.strip(',')
            experiment_str += ("(%d, ["%seconds_to_mu(t*1e-3)) + time_events_str + "]),"

        experiment_str = experiment_str.strip(',')

        return "["+experiment_str+"]"

    def cycle_init(self):
        expid = {
            "class_name": "QuantumPlayerCycleInit",
            "file": "qplayer_cycle_init.py",
            "arguments": {},
            "log_level": 0,
            "repo_rev": "N/A",
        }
        self.initializing = True
        self.master_scheduler.submit(pipeline_name="main", expid=expid, priority=0, due_date=None, flush=False)
        print("Play artiq cycle init first")

    def play_once(self, run_id):
        expid = {
            "class_name": "QuantumPlayer",
            "file": "qplayer.py",
            "arguments": {"sequence": self.exp_str, "last_delay": self.last_delay},
            "log_level": 0,
            "repo_rev": "N/A",
        }

        self.master_scheduler.submit(pipeline_name="main", expid=expid, priority=0, due_date=None, flush=False)
        print("Play artiq sequence once")

    def artiq_schedule_setup(self, schedule):
        self.experiment_schedule.clear()
        self.experiment_schedule.update(schedule)
        return self.experiment_schedule

    def artiq_schedule_update(self, mod: dict):

        queue_size = len(self.experiment_schedule)

        if 'path' in mod and len(mod['path']) == 0: # If the number of tasks changes
            print("ARTIQ queue size: %d" % queue_size)
        if mod['action'] == 'delitem': # Item has been deleted
            if queue_size < 2: # We keep the length of the queue to two elements or fewer.
                if self.initializing:
                    self.initializing = False
                    print("Cycle Init Finished")
                else:
                    self.sequence_finished()

    def stop(self):
        # TODO
        pass


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
        return {"name": self.name, "class": self.__class__.__name__}


class TTLOutARTIQCard(ARTIQCard):
    num_channels = 16
    type = utils.DigitalTrack


class ZotinoARTIQCard(ARTIQCard):
    num_channels = 32
    type = utils.AnalogTrack

    def __init__(self, name, channels, samplerate):
        super().__init__(name, channels)
        self.samplerate = samplerate
