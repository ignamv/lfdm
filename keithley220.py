from lantz import Feat, Q_, Action
from lantz.visa import GPIBVisaDriver

class Keithley220 (GPIBVisaDriver):
    RECV_TERMINATION = '\r\n'
    SEND_TERMINATION = ''

    def initialize(self):
        super().initialize()
        # Send data without prefix
        self.send('G1X')

    @Feat()
    def data(self):
        return list(map(float, self.recv().split(',')))

    @Feat()
    def status(self):
        return '220' + self.query('U0X')

    @Feat(values={True: 1, False: 0})
    def output(self):
        return int(self.status[4])

    @output.setter
    def output(self, enable):
        self.send('F{}X'.format(enable))

    @Action()
    def clear(self):
        self.send('DCL')

    @Feat(units='V')
    def voltage_limit(self):
        return self.data[1]
    
    @voltage_limit.setter
    def voltage_limit(self, value):
        self.send('V{:.2E}X'.format(value))

    @Feat(values={'auto': 0, 'nA': 1, '10nA': 2, '100nA': 3, '1uA': 4, 
        '10uA': 5, '100uA': 6, '1mA': 7, '10mA': 8, '100mA': 9})
    def range(self):
        return int(self.status[9])

    @range.setter
    def range(self, value):
        self.send('R{}X'.format(value))

    @Action()
    def execute(self):
        self.send('X')

    @Feat(units='A')
    def current(self):
        return self.data[0]

    @current.setter
    def current(self, value):
        self.send('I{:.3E}X'.format(value))

    def finalize(self):
        self.output = False
        super().finalize()

if __name__ == '__main__':
    from lantz.log import log_to_screen, DEBUG
    log_to_screen(DEBUG)
    inst = Keithley220('GPIB0::12::INSTR')
    inst.initialize()
    print(repr(inst.status))
    inst.finalize()

