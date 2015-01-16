from lantz import Feat, Q_, Action
from lantz.visa import GPIBVisaDriver

class HP4277A (GPIBVisaDriver):
    @Action()
    def bias_voltage(self, value):
        self.send('BI{:+02.2f}EN'.format(Q_(value).to('V').magnitude))

    def __del__(self):
        self.bias_voltage(Q_(0, 'V'))

if __name__ == '__main__':
    inst = HP4277A('GPIB0::17::INSTR')
    inst.initialize()
    inst.bias_voltage(Q_(0.12, 'V'))
    input()
    inst.bias_voltage(Q_(-0.12, 'V'))
    input()
    inst.bias_voltage(Q_(0, 'V'))

