import hardware
import sequence

class Scheduler:

    def __init__(self, seq: sequence.Sequence, hw: hardware.Hardware):
        self.sequence = seq
        self.hardware = hw

    def play_once(self):
        print("Run single")
        csequence = self.sequence.playlist.compile_active_playlist()
        self.hardware.process_sequence(csequence)
        self.hardware.play_once()

    def play(self):
        print("Run continuous")
        csequence = self.sequence.playlist.compile_active_playlist()
        self.hardware.process_sequence(csequence)
        self.hardware.play()

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