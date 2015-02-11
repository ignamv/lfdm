from lantz import Feat, Q_, Action, DictFeat
from lantz.visa import GPIBVisaDriver
import numpy as np
import re

class HP4277A (GPIBVisaDriver):
    RECV_TERMINATION = ''
    def initialize(self):
        super().initialize()
        # Set output format
        self.send('F1')

    #FR10.0ENA1B3C1D0F1M2P0R4S0T1U1V1X0BI+0.00EN
    learn_re = re.compile(r'FR([0-9.]+)ENA([1-5])B([1-3])C([1-3])D([01])'\
            'F([1-4])M([1-3])P([01])R([1-8])S([01])T([12])U([01])V([12])'\
            'X([01])BI([+\-0-9.]+)EN')
    @Feat()
    def learn(self):
        return self.learn_re.match(self.learn_raw).groups()

    @Feat()
    def learn_raw(self):
        return self.query('LN')

    @Feat(units='V', limits=(-40, 40))
    def bias_voltage(self):
        return float(self.learn[14])

    @bias_voltage.setter
    def bias_voltage(self, value):
        self.send('BI{:+02.2f}EN'.format(value))

    @Feat(units='kHz', limits=(10, 1000))
    def frequency(self):
        return float(self.learn[0])

    @frequency.setter
    def frequency(self, value):
        self.send('FR{:3.1f}EN'.format(value))

    @Feat(values=dict(L='1', C='2', fastL='3', fastC='4', Z='5'))
    def functionA(self):
        return self.learn[1]

    @functionA.setter
    def functionA(self, value):
        self.send('A' + value)

    @Feat(values=dict(D='1', Q='2', ESR='3'))
    def functionB(self):
        return self.learn[2]

    @functionB.setter
    def functionB(self, value):
        self.send('B' + value)

    @Feat(values=dict(auto='1', series='2', parallel='3'))
    def circuit_mode(self):
        return self.learn[3]

    @circuit_mode.setter
    def circuit_mode(self, value):
        self.send('C' + value)

    @Feat(values=dict(slow='1', medium='2', fast='3'))
    def speed(self):
        return self.learn[6]

    @speed.setter
    def speed(self, value):
        self.send('M' + value)

    @Feat(values=dict(off='0', on='1'))
    def autorange(self):
        return self.learn[11]

    @autorange.setter
    def autorange(self, value):
        self.send('U' + value)

    @Feat(values=dict(off='0', on='1'))
    def data_ready(self):
        return self.learn[4]

    @data_ready.setter
    def data_ready(self, value):
        self.send('D' + value)

    @Feat(values=dict(low='0', high='1'))
    def test_signal_level(self):
        return self.learn[12]

    @test_signal_level.setter
    def test_signal_level(self, value):
        self.send('V' + value)

    measure_re = re.compile(r'(?P<circuit_mode>[PS])(?P<statusA>[NDOUCB])'\
            '(?P<functionA>[LCZ])(?P<valueA>[+\-0-9.E]+)(\r\n|,)'\
            '(?P<statusB>[NDOUCB])(?P<functionB>[DQRGTN])'\
            '(?P<valueB>[+\-0-9.E]+)')
    def display(self):
        #_, statusA, funcA, dispA, _, statusB, funcB, dispB = \
        match = self.measure_re.match(self.recv())
        return match.groupdict()

    displays = ['A', 'B']
    @DictFeat(values=dict(normal='N', deviation='D', overflow='O',
        underflow='U', change_function='C', blank='B'), keys=displays)
    def display_status(self, key):
        return self.display()['status' + key]

    @Action()
    def execute(self):
        self.send('EX')

    @Feat(units='ohm')
    def impedance(self):
        self.functionA = 'Z'
        self.execute()
        # Wait for data ready
        while self.read_status() & 1 == 0:
            print(self.read_status())
            pass
        disp = self.display
        for dd in self.displays:
            if self.display_status[disp] != 'normal':
                raise Exception('Status {}: {}'.format(disp,
                    self.display_status[disp]))
        ret = float(disp['valueA']) + 0j
        ret *= np.exp(1j * deg2rad(float(disp['valueB'])))
        return ret

    def measure_stable(self, epsilon=1e-2):
        meas2 = self.measure
        while True:
            meas1 = meas2
            meas2 = self.measure
            if abs((meas1[0]-meas2[0])/meas2[0]) < epsilon:
                return meas2

    def finalize(self):
        self.bias_voltage = Q_(0, 'V')

if __name__ == '__main__':
    from lantz.log import log_to_screen, DEBUG
    log_to_screen(DEBUG)
    inst = HP4277A('GPIB0::17::INSTR')
    inst.initialize()
    feats = inst.refresh()
    for k in feats.keys():
        print('{}: {}'.format(k, feats[k]))
    print(inst.read_status())
    inst.finalize()

