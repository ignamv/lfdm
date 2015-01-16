from lantz import Feat, Q_, Action, LOGGER
from lantz.visa import GPIBVisaDriver
from lantz.log import log_to_screen, DEBUG
from time import sleep, time
from lantz.driver import _DriverType

def SetterFeat(*args, **kwargs):
    feat = Feat(*args, **kwargs)
    def inner(function):
        return feat.setter(function)
    return inner

def HP8112ADictFeat(command, values):
    def setter(self, value):
        self.send(command + value)
    def getter(self):
        return self.query('I' + command)[len(command):]
    feat = Feat(values=values)
    feat.setter(setter)
    feat.getter(getter)
    return feat

def HP8112AFeat(command, limits=None):
    units = str(limits[1].units)
    def setter(self, value):
        self.send(command + ' {:~}'.format(Q_(value, units)))
    def getter(self):
        return HP8112A.process_response(self.query('I' + command))
    limits = (limits[0].to(units).magnitude,
              limits[1].to(units).magnitude)
    feat = Feat(limits=limits, units=units)
    feat.setter(setter)
    feat.getter(getter)
    return feat

class HP8112A (GPIBVisaDriver):
    RECV_TERMINATION = '\r\n '
    SEND_TERMINATION = '\r\n'
    QUERY_PAUSE = .2

    BUFFER_NOT_EMPTY = 0x80

    @staticmethod
    def process_response(response):
        # Skip first word, fix units
        space = response.index(" ") + 1
        return Q_(response[space:].strip().lower().replace('v', 'V'))

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        self.send(command, *send_args)
        while self.visa.read_stb(self.vi) & HP8112A.BUFFER_NOT_EMPTY != 0:
            # Wait for BUFFER NOT EMPTY bit to clear
            pass
        return self.recv(*recv_args)

    def initialize(self):
        self._init_attributes = { 
                'TMO_VALUE': 5000,   # Increase timeout
                'SEND_END_EN': 0}    # Do not terminate commands with EOI signal
        super().initialize()

    @Feat()
    def settings(self):
        return self.query('CST')

    @SetterFeat(values=dict(normal='1', trigger='2', gate='3', ewid='4', 
        ebur='5'))
    def trigger_mode(self, value):
        self.send('M' + value)

    @Feat()
    def trigger(self):
        self.send('GET')

    period = HP8112AFeat('PER', (Q_(20, 'ns'), Q_(950, 'ms')))
    delay = HP8112AFeat('DEL', (Q_(75, 'ns'), Q_(950, 'ms')))
    width = HP8112AFeat('WID', (Q_(10, 'ns'), Q_(950, 'ms')))
    leading_edge = HP8112AFeat('LEE', (Q_(6.5, 'ns'), Q_(95, 'ms')))
    trailing_edge = HP8112AFeat('TRE', (Q_(6.5, 'ns'), Q_(95, 'ms')))
    high_level = HP8112AFeat('HIL', (Q_(-7.9, 'V'), Q_(8, 'V')))
    low_level = HP8112AFeat('LOL', (Q_(-8, 'V'), Q_(7.9, 'V')))


if __name__ == '__main__':
    #inst = HP8112A('GPIB0::11::INSTR', library_path=r'C:\Archivos de programa\National Instruments\RT Images\NI-VISA\2.5.1\visa32.dll')
    #inst = HP8112A('GPIB0::11::INSTR', library_path=r'C:\Archivos de programa\VISA\winnt\agvisa\agbin\visa32.dll')
    #inst = HP8112A('GPIB0::11::INSTR', library_path='C:\\lantz\\system32\\visa32.dll')
    inst = HP8112A('GPIB0::11::INSTR')
    inst.initialize()
    print(inst.period)
    print(inst.delay)
    print(inst.width)
    print(inst.leading_edge)
    print(inst.settings)
