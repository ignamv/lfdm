from lantz import Feat, DictFeat, Action, Q_
from lantz.visa import MessageVisaDriver
from lantz.ui.app import start_test_app
from stringparser import Parser
from struct import unpack
import numpy as np
from time import sleep, time
import pyvisa.constants as vi

format_strings = dict(boolean='{:d}', nr1='{:d}', nr2='{:f}', nr3='{:E}',
        nrf='{:e}')

def MyFeat(command, fmt, *args, **kwargs):
    parse = Parser(format_strings[fmt])

    def setter(self, value):
        self.send(command + ' ' + format_strings[fmt].format(value))

    def getter(self):
        return parse(self.query(command + '?').strip())

    return Feat(*args, fset=setter, fget=getter, read_once=True, **kwargs)

def MyChanFeat(command, fmt, *args, **kwargs):
    parse = Parser(format_strings[fmt])

    def setter(self, channel, value):
        self.send(command.format(channel) + ' ' + 
                format_strings[fmt].format(value))

    def getter(self, channel):
        return parse(self.query(command.format(channel) + '?').strip())

    return DictFeat(*args, fset=setter, fget=getter,
            keys=[1, 2], read_once=True, **kwargs)

class GwinstekGDS2062(MessageVisaDriver):
    channels = [1, 2]
    xdivisions = 20 # Only displays 10 on screen
    ydivisions = 10 # Only displays 8 on screen

    @Feat()
    def idn(self):
        return self.query('*IDN?')


    # TODO: make record_length sane. Reading returns number of points, but 
    # only 0 or 1 can be written
    record_length = MyFeat(':acquire:length', 'boolean')
    averaging = MyFeat(':acquire:average', 'nr1', values={2**ii: ii
        for ii in range(1, 9)})
    mode = MyFeat(':acquire:mode', 'nr1', values=dict(normal=0, peak=1,
        average=2))
    bandwidth_limit = MyChanFeat(':channel{}:bwlimit', 'nr1',
            values={True: 1, False: 0})
    coupling = MyChanFeat(':channel{}:coupling', 'nr1',
            values=dict(ac=0, dc=1, ground=2))
    display = MyChanFeat(':channel{}:display', 'nr1', 
            values={True: 1, False: 0})
    invert = MyChanFeat(':chan{}:inv', 'nr1', 
            values={True: 1, False: 0})
    offset = MyChanFeat(':channel{}:offset', 'nr3', units='V')
    voltage_scales = Q_(np.concatenate(tuple(np.array([1., 2., 5.]) * 10**ii
        for ii in range(-3, 1)))[1:], 'V')
    voltage_scale = MyChanFeat(':channel{}:scale', 'nr3', units='V')
    trigger_level = MyFeat(':trig:lev', 'nr3', units='V')
    trigger_mode = MyFeat(':trigger:mode', 'nr1', values=dict(auto_level=0, 
        auto=1, normal=2, single=3))
    trigger_couple = MyFeat(':trigger:couple', 'nr1', values=dict(ac=0, dc=1))
    trigger_slope = MyFeat(':trig:slop', 'nr1', values=dict(rising=0,
        falling=1))
    trigger_source = MyFeat(':trigger:source', 'nr1', values={1: 0, 2: 1, 3: 2,
        4: 3, 'external': 4, 'line': 5})
    trigger_type = MyFeat(':trigger:type', 'nr1', values=dict(edge=0, video=1,
        pulse=2, delay=3))
    delay = MyFeat(':timebase:delay', 'nr3', units='s')
    time_scales = Q_(np.concatenate(tuple(np.array([1., 2.5, 5.]) * 10**ii
        for ii in range(-9, 2)))[:-2], 's')
    time_scale = MyFeat(':timebase:scale', 'nr3', units='s')
    
    @Action()
    def fit_time(self, time):
        """Find smallest time scale that fits time in one acquisition"""
        self.time_scale = next(tt for tt in self.time_scales 
                if tt * self.xdivisions >= time)

    @Action()
    def fit_voltage(self, voltage, channel):
        """Find smallest time scale that fits time in one acquisition"""
        self.voltage_scale[channel] = next(vv for vv in self.voltage_scales 
                if vv * self.ydivisions >= voltage)

    @Action()
    def run(self):
        self.send(':run')

    @Action()
    def stop(self):
        self.send(':stop')

    setup_memories = list(range(1, 21))
    @Action()
    def recall_setup(self, memory):
        if memory not in self.setup_memories:
            raise RuntimeError('Invalid memory: {}'.format(memory))
        self.send(':memory{}:recall:setup'.format(memory))

    @Action()
    def save_setup(self, memory):
        if memory not in self.setup_memories:
            raise RuntimeError('Invalid memory: {}'.format(memory))
        self.send(':memory{}:save:setup'.format(memory))

    @Action()
    def acquire(self, channels, process=True):
        ret = []
        for channel in channels:
            if channel not in self.channels:
                raise RuntimeError('Invalid channel: {}'.format(channel))
            self.send(':acquire{}:memory?'.format(channel))
            # Response format in programmer's manual page 29
            data = self.read_block()
            if all(dd == 0 for dd in data[8:]):
                # Received all zeros
                raise RuntimeError('Bad acquisition')
            ret.append(data)
        if not process:
            return ret
        else:
            return self.process_data(ret)

    def process_data(self, data):
        ret = dict()
        for dd in data:
            channel = dd[4]
            deltaT = unpack('>f', dd[:4])
            raw = np.frombuffer(dd[8:], dtype=np.int16)
            range = np.iinfo(raw.dtype).max - np.iinfo(raw.dtype).min
            ret[channel] = raw / range * self.voltage_scale[channel] * 10
        ret['time'] = deltaT * np.arange(len(raw))
        return ret

if __name__ == '__main__':
    from lantz.log import log_to_screen, DEBUG
    import matplotlib
    print(matplotlib.get_backend())
    print(matplotlib.get_configdir())
    from matplotlib import pyplot as plt
    log_to_screen(DEBUG)
#   inst = GwinstekGDS2062('ASRL6::INSTR',
#       library_path=r'C:\windows\system32\visa32.Agilent Technologies.dll')
    inst = GwinstekGDS2062('ASRL5::INSTR')
    inst.initialize()
    print(inst.refresh())
    print('Presione una tecla')
    input()
    from time import time
    for largo in [0, 1]:
        inst.record_length = largo
        inicial = time()
        inst.acquire([1,2])
        final = time()
        print('Con record_length={} tarda {}s'.format(largo, final - inicial))
