import hardware
import sequence

from PyQt5.QtCore import QThread


class Scheduler:

    def __init__(self, seq: sequence.Sequence, hw: hardware.Hardware):
        self.sequence = seq
        self.hardware = hw
        self.hardware.add_sequence_end_listener(self.sequence_finished)

        # TODO: run_id should be loaded and saved into a database
        self.run_id = 0
        self.run_continuous = False

    def play_once(self):
        print("Run single")
        csequence = self.sequence.playlist.compile_active_playlist()
        self.hardware.process_sequence(csequence, self.run_id)
        self.hardware.play_once(self.run_id)
        self.run_id += 1

    def play_continuous(self):
        print("Run continuous")
        self.run_continuous = True
        self.play_once()

    def iterate(self):
        pass

    def stop(self):
        self.run_continuous = False
        self.hardware.stop()

    def shuffle_on(self):
        pass

    def shuffle_off(self):
        pass

    # This function is called when the hardware is ready to receive the next new sequence
    def sequence_finished(self):
        print("scheduler: Sequence finished")
        if self.run_continuous:
            self.play_once()
