from lantz import Feat, Q_
from lantz.serial import SerialDriver

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

    def measure_stable(self, epsilon=1e-2):
        meas2 = self.measure
        while True:
            meas1 = meas2
            meas2 = self.measure
            if abs((meas1[0]-meas2[0])/meas2[0]) < epsilon:
                return meas2

        

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

