from lantz import Feat, DictFeat, Q_, Action
from lantz.visa import GPIBVisaDriver

columns = list(range(1,6))
rows = list(range(1,5))
class Keithley705 (GPIBVisaDriver):
    @Action()
    def matrix_mode(self):
        self.send('A0X')

    columns = columns
    rows = rows

    @DictFeat(read_once=True, values={True: True, False: False},
            keys=[(col, row) for col in columns 
                             for row in rows])
    def channel(self, key):
        return self.query('B{:02d}{:01d}U0X'.format(col, row))[-1] == '1'

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
            key = (int(col), int(row))
            ret[key] = (status == '1')
            self._lantz_features['channel'].set_cache(self, ret[key], key)
        return ret

    @Action()
    def execute(self):
        self.send('X')

    @Feat()
    def status(self):
        return '705' + self.query('U4X')

    @Action()
    def reset(self):
        self.send('RX')
        for row in self.rows:
            for column in self.columns:
                self._lantz_features['channel'].set_cache(self, False, 
                        (column, row))

    def initialize(self):
        super().initialize()
        # Send channel buffer state without prefix
        self.send('G3X')
        self.matrix_mode()

    def finalize(self):
        self.reset()
        super().finalize()

if __name__ == '__main__':
    from lantz.log import log_to_screen, DEBUG
    log_to_screen(DEBUG)
    inst = Keithley705('GPIB0::29::INSTR')
    inst.initialize()
    inst.reset()
    inst.channel[(4,3)] = True
    inst.channel[(2,1)] = True
    chan = inst.refresh('channel')
    print(chan)
    print([k for k in chan.keys() if chan[k]])
    inst.reset()
