from artiq.experiment import *


class QuantumPlayerCycleInit(EnvExperiment):
    def build(self):
        self.setattr_device("core")
        self.setattr_device("led0")
        self.setattr_device('zotino0')

    @kernel
    def run(self):
        self.core.reset()
        delay(10*ms)
        self.zotino0.init()
        self.led0.pulse(250*ms)
        delay(125*ms)
        self.led0.pulse(125*ms)
        delay(125*ms)
        self.led0.pulse(125*ms)
        delay(250*ms)
