from lantz import Feat, DictFeat, Action
from lantz.visa import GPIBVisaDriver
from lantz.visa import MessageVisaDriver
from stringparser import Parser
from struct import unpack
import numpy as np
from time import sleep

def MyFeat(command, fmt, *args, **kwargs):
    format_strings = dict(boolean='{:d}', nr1='{:d}', nr2='{:f}', nr3='{:E}',
            nrf='{:e}')
    parse = Parser(format_strings[fmt])

    def setter(self, value):
        self.send(command + ' ' + format_strings[fmt].format(value))

    def getter(self):
        return parse(self.query(command + '?').strip())

    return Feat(*args, fset=setter, fget=getter, **kwargs)

def MyChanFeat(command, fmt, *args, **kwargs):
    parse = Parser(format_strings[fmt])

    def setter(self, channel, value):
        self.send(command.format(channel) + ' ' + 
                format_strings[fmt].format(value))

    def getter(self, channel):
        return parse(self.query(command.format(channel) + '?').strip())

    return DictFeat(*args, fset=setter, fget=getter, **kwargs)

class GwinstekGDS2062(MessageVisaDriver):

    @Feat()
    def idn(self):
        return self.query('*IDN?')

    # TODO: make this sane. Reading returns number of points, but only 0 or 1
    # can be written
    record_length = MyFeat(':acquire:length', 'boolean')
    offset = MyChanFeat(':channel{}:offset', 'nr3', units='V')
    scale = MyChanFeat(':channel{}:scale', 'nr3', units='V')

    @Action()
    def run(self):
        self.send(':run')

    @Action()
    def stop(self):
        self.send(':stop')

    def acquire(self, channel):
        if channel not in [1, 2]:
            raise KeyError('Invalid channel {}'.format(channel))
        self.send(':acquire{}:memory?'.format(channel))
        # Response format in programmer's manual page 29
        data = self.read_block()
        deltaT = unpack('>f', data[:4])
        channel_ = data[4]
        if channel_ != channel:
            raise RuntimeError('Invalid channel reply: {}'.format(channel_))
        # 3 reserved bytes
        raw = np.frombuffer(data[8:], dtype=np.int16)
        range = np.iinfo(raw.dtype).max - np.iinfo(raw.dtype).min
        return raw / range * self.scale[channel] * 10

if __name__ == '__main__':
    from lantz.log import log_to_screen, DEBUG
    from matplotlib import pyplot as plt
    log_to_screen(DEBUG)
#   inst = GwinstekGDS2062('ASRL6::INSTR',
#       library_path=r'C:\windows\system32\visa32.Agilent Technologies.dll')
    inst = GwinstekGDS2062('ASRL5::INSTR')
    inst.initialize()
    print(inst.idn)
    inst.record_length = 0
    print(inst.record_length)
    print(inst.offset[1])
    print(inst.scale[1])
    inst.stop()
    ch1 = inst.acquire(1)
    sleep(.7777)
    ch2 = inst.acquire(2)
    inst.run()
    np.savetxt('salida.txt', ch1)
    plt.plot(ch1)
    plt.hold(True)
    plt.plot(ch2)
    plt.show()

