from artiq.experiment import EnvExperiment,kernel,ms
class PyPlayerGeneratedExperiment{{id}}(EnvExperiment):
    def build(self):
        self.setattr_device('core')
        for i in range(16):
            self.setattr_device('ttl%d'%i)
        self.setattr_device('zotino0')
    @kernel
    def run(self):
        self.core.reset()
        self.zotino0.init()
        delay(10*ms)
{{experiment}}