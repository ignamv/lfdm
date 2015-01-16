from lantz import Feat, Q_, Action
from lantz.visa import GPIBVisaDriver

class Keithley617 (GPIBVisaDriver):
    RECV_TERMINATION = '\r\n'
    SEND_TERMINATION = ''

    def initialize(self):
        super().initialize()
        # Return data without prefix
        self.send('G1')
        # Continuous trigger on talk
        self.send('T0')

    @Feat(values=dict(volts=0, amps=1, ohms=2, coulombs=3))
    def function(self):
        return int(self.status[3])

    @function.setter
    def function(self, func):
        self.send('F{}X'.format(func))

    @Feat(units='V')
    def voltage(self):
        self.function = 'volts'
        self.execute()
        return self.recv()

    def stable_voltage(self, epsilon=1e-3):
        ret = self.voltage
        while True:
            last = ret
            ret = self.voltage
            if abs(last-ret)/ret < epsilon:
                return ret

    @Action()
    def execute(self):
        self.send('X')

    @Feat(values=dict(auto=0))
    def range(self):
        return int(self.status[4:6])

    @range.setter
    def range(self, value):
        self.send('R{}X'.format(value))

    @Feat(values={True:1, False:0})
    def zero_check(self):
        return int(self.status[6])

    @zero_check.setter
    def zero_check(self, enable):
        self.send('Z{}X'.format([0, 1][bool(enable)]))

    @Feat(values={True:1, False:0})
    def zero_correct(self):
        return int(self.status[7])

    @zero_correct.setter
    def zero_correct(self, enable):
        self.send('C{}X'.format([0, 1][bool(enable)]))

    @Feat(values=dict(electrometer=0, vsource=1))
    def display_mode(self):
        return int(self.status[13])

    @display_mode.setter
    def display_mode(self, mode):
        self.send('D{}X'.format(mode))

    @Feat(values=dict(electrometer=0, buffer=1, max=2, min=3, vsource=4))
    def reading_mode(self):
        return int(self.status[11])

    @reading_mode.setter
    def reading_mode(self, mode):
        self.send('B{}X'.format(mode))

    @Feat()
    def status(self):
        return self.query('U0X')

if __name__ == '__main__':
    from lantz.log import log_to_screen, DEBUG
    log_to_screen(DEBUG)
    inst = Keithley617('GPIB0::28::INSTR')
    inst.initialize()
    print(inst.query('U0X'))
    print(inst.display_mode)
    print(inst.reading_mode)
    print(inst.range)
    print(inst.function)
    inst.finalize()
