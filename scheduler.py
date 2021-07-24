import hardware
import sequence

class Scheduler:

    def __init__(self, seq: sequence.Sequence, hw: hardware.Hardware):
        self.sequence = seq
        self.hardware = hw
        # TODO: run_id should be loaded and saved into a database
        self.run_id = 0


    def play_once(self):
        print("Run single")
        csequence = self.sequence.playlist.compile_active_playlist()
        self.hardware.process_sequence(csequence, self.run_id)
        self.hardware.play_once(self.run_id)
        self.run_id += 1

    def play(self):
        print("Run continuous")
        pass

    def iterate(self):
        pass

    def stop(self):
        self.hardware.stop()

    def shuffle_on(self):
        pass

    def shuffle_off(self):
        pass

    def sequence_finished(self):
        print("Sequence finished")