from lantz import Feat, Q_, Action
from lantz.serial import SerialDriver
import numpy as np

class GwinstekLCR8110G (SerialDriver):
    ENCODING = 'ascii'
    RECV_TERMINATION = '\n'
    SEND_TERMINATION = '\n'

    @Feat()
    def idn(self):
        return self.query('*IDN?')

    @Feat(units="Hz")
    def frequency(self):
        return self.query(':meas:freq?')

    @frequency.setter
    def frequency(self, value):
        self.send(':meas:freq {:e}'.format(value))

    @Feat(values={'series': 'ser', 'parallel': 'par'})
    def equivalent_circuit(self):
        return ['par', 'ser'][int(self.query(':meas:equ-cct?'))]
    def eequivalent_circuit(self):
        return self.query(':meas:equ-cct?')

    @equivalent_circuit.setter
    def equivalent_circuit(self, value):
        self.send(':meas:equ-cct {}'.format(value))

    @Feat(units='V')
    def drive_level(self):
        return self.query(':meas:lev?')

    @drive_level.setter
    def drive_level(self, value):
        self.send(':meas:lev {:e}'.format(value))

    @Feat()
    def measure(self):
        first, second = map(float, self.query(':meas:trig').split(","))
        return (first, second)

    @Action()
    def measure_stable(self, epsilon=1e-2):
        meas2 = self.measure
        while True:
            meas1 = meas2
            meas2 = self.measure
            if np.linalg.norm(np.subtract(meas2, meas1)) / np.linalg.norm(
                    meas2) < epsilon:
                return meas2

    @Feat(values=dict(C=0, L=1, X=2, B=3, Z=4, Y=5))
    def function1(self):
        return self.query(':meas:func:major?')

    @function1.setter
    def function1(self, value):
        self.send(':meas:func:major {:d}'.format(value))

    @Feat(values=dict(Q=0, D=1, R=2, G=3))
    def function2(self):
        return self.query(':meas:func:minor?')

    @function2.setter
    def function2(self, value):
        self.send(':meas:func:minor {:d}'.format(value))

    @Feat(values=dict(max=0, fast=1, med=2, slow=3))
    def speed(self):
        return self.query(':meas:speed?')

    @speed.setter
    def speed(self, value):
        self.send(':meas:speed {:d}'.format(value))

if __name__ == '__main__':
    inst = GwinstekLCR8110G(port=0, timeout=5)
    inst.initialize()
    print(inst.idn)
    print(inst.frequency)
    print(inst.equivalent_circuit)
    print(inst.eequivalent_circuit())
    input()
    inst.equivalent_circuit = 'series'
    print(inst.eequivalent_circuit())
    input()
    inst.equivalent_circuit = 'parallel'
    print(inst.eequivalent_circuit())
    input()
    print(inst.drive_level)
    print(inst.measure)

