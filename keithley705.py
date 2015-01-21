from lantz import Feat, DictFeat, Q_, Action
from lantz.visa import GPIBVisaDriver

class Keithley705 (GPIBVisaDriver):
    @Action()
    def matrix_mode(self):
        self.send('A0')

    @DictFeat(values={True: True, False: False},
            keys=[(col, row) for col in range(1, 6) for row in range(1, 5)])
    def channel(self, key):
        return self.channels[key]

    @Action()
    def open(self, channel):
        self.channel[channel] = False

    @Action()
    def close(self, channel):
        self.channel[channel] = True

    @channel.setter
    def channel(self, key, value):
        col, row = key
        self.send('{}0{}{}X'.format(['N', 'C'][value], col, row))

    @Feat()
    def channels(self):
        ret = dict()
        data = self.query('U1X').split(',')
        for channel, status in zip(data[::2], data[1::2]):
            col, row = channel.split(':')
            ret[(int(col), int(row))] = (status == '1')
        return ret

    @Action()
    def execute(self):
        self.send('X')

    @Action()
    def reset(self):
        self.send('RX')

    def initialize(self):
        super().initialize()
        # Send channel buffer state without prefix
        self.send('G3X')

    def finalize(self):
        self.reset()
        super().finalize()

if __name__ == '__main__':
    from lantz.log import log_to_screen, DEBUG
    log_to_screen(DEBUG)
    inst = Keithley705('GPIB0::29::INSTR')
    inst.initialize()
    inst.channel[(4,3)] = True
    inst.channel[(2,1)] = True
    chan = inst.channels
    print(chan)
    print([k for k in chan.keys() if chan[k]])
    inst.reset()
