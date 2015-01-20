from lantz import Driver, Feat
from time import sleep

class DummyGen(Driver):
    def initialize(self):
        super().initialize()
        self._voltage = 3

    @Feat()
    def voltage(self):
        sleep(3)
        return self._voltage

    @voltage.setter
    def voltage(self, value):
        sleep(3)
        self._voltage = value

    @Feat()
    def current(self):
        sleep(3)
        return self._voltage/1e3
