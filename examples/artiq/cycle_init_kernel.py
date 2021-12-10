from artiq.experiment import *


class CycleInit(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("led0")

    @kernel
    def run(self):
        self.core.reset()

        # Pulse a few times to give visual feedback and start with some slack
        self.led0.pulse(250*ms)
        delay(125*ms)
        self.led0.pulse(125*ms)
        delay(125*ms)
        self.led0.pulse(125*ms)
        delay(250*ms)
