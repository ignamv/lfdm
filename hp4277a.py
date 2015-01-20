from lantz import Feat, Q_, Action
from lantz.visa import GPIBVisaDriver
from re import match

class HP4277A (GPIBVisaDriver):
    RECV_TERMINATION = ''
    @Action()
    def bias_voltage(self, value):
        self.send('BI{:+02.2f}EN'.format(Q_(value).to('V').magnitude))

    @Action()
    def frequency(self, value):
        self.send('FR{:3.1f}EN'.format(Q_(value).to('kHz').magnitude))

    @Feat()
    def measure(self):
        for ii in range(5):
            recv = self.recv()
            if recv[1] == 'N':
                break
        if recv[1] in ['O', 'U']:
            raise Exception('Overflow')
        groups = match(r'.{3}([+\-0-9.eE]+)\r\n.{2}([+\-0-9.eE]+)',
                recv).groups()
        return (float(groups[0]), float(groups[1]))

    def measure_stable(self, epsilon=1e-2):
        meas2 = self.measure
        while True:
            meas1 = meas2
            meas2 = self.measure
            if abs((meas1[0]-meas2[0])/meas2[0]) < epsilon:
                return meas2

    def finalize(self):
        self.bias_voltage(Q_(0, 'V'))

if __name__ == '__main__':
    inst = HP4277A('GPIB0::17::INSTR')
    inst.initialize()
    inst.frequency(Q_(90, 'kHz'))
    print(inst.measure())
    inst.finalize()

