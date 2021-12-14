from artiq.experiment import EnvExperiment,kernel,ms,PYONValue

DIGITAL=0
ANALOG =1

class QuantumPlayer(EnvExperiment):
    def build(self):
        self.setattr_device('core')
        Nttl = 32
        for i in range(Nttl):
            self.setattr_device('ttl%d'%i)
        self.setattr_device('zotino0')
        self.ttls = [self.get_device("ttl%d"%i) for i in range(Nttl)]
        self.setattr_argument("sequence", PYONValue(default=[]))
        
    def prepare(self):
        self.last_delay = 0

    @kernel
    def run(self):
        #self.core.reset()
        delay(10*ms)
        print("Pre Init", self.core.mu_to_seconds(now_mu() - self.core.get_rtio_counter_mu()))
        self.zotino0.init(blind=True)
        print("After Init", self.core.mu_to_seconds(now_mu() - self.core.get_rtio_counter_mu()))
        delay(10*ms)

        tprev = 0
        for time, events in self.sequence:
            delay_mu(time-tprev)
            for channel_type, channel_num, value in events:
                if channel_type == DIGITAL:
                    ttl = self.ttls[channel_num]
                    if value == 1:
                        ttl.on()
                    else:
                        ttl.off()

                if channel_type == ANALOG:
                    self.zotino0.write_dac_mu(channel_num, value)
                    self.zotino0.load()
            tprev = time
            
        # Add last delay
        #delay_mu(self.last_delay)
        print("After Execution", self.core.mu_to_seconds(now_mu() - self.core.get_rtio_counter_mu()))
