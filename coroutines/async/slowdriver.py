from lantz import Driver, Feat, Q_
from time import sleep

class SlowDriver(Driver):
    """Simulate a slow voltage source/ammeter connected to 1kOhm resistor"""

    def __init__(self, delay=3):
        """delay: each set/get takes this many seconds"""
        super().__init__()
        self.delay = delay
        self._voltage = 0

    @Feat(units='V')
    def voltage(self):
        sleep(self.delay)
        return self._voltage

    @voltage.setter
    def voltage(self, value):
        sleep(self.delay)
        self._voltage = value

    @Feat(units='A')
    def current(self):
        sleep(self.delay)
        return self._voltage/1e3
