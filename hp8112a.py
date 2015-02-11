from lantz import Feat, Q_, Action, LOGGER
from lantz.driver import _DriverType
from lantz.log import log_to_screen, DEBUG
from lantz.ui.app import start_test_app
from lantz.visa import GPIBVisaDriver
from time import sleep, time
import pyvisa.constants
import re

def HP8112ADictFeat(command, values):
    def setter(self, value):
        self.send(command + value)
    def getter(self):
        return self.query('I' + command)[len(command):]
    feat = Feat(values=values, read_once=True)
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
    feat = Feat(limits=limits, units=units, read_once=True)
    feat.setter(setter)
    feat.getter(getter)
    return feat

class HP8112A (GPIBVisaDriver):
    RECV_TERMINATION = '\r\n'
    SEND_TERMINATION = '\r\n'

    BUFFER_NOT_EMPTY = 0x80

    @staticmethod
    def process_response(response):
        groups = re.match(r' *\w+ (?P<value>[+\-0-9.]+) (?P<units>\w+)',
                response).groupdict()
        return Q_(float(groups['value']),
                groups['units'].lower().replace('v', 'V'))

    def query(self, command, *, send_args=(None, None), recv_args=(None, None)):
        self.send(command, *send_args)
        while self.read_status() & HP8112A.BUFFER_NOT_EMPTY != 0:
            # Wait for BUFFER NOT EMPTY bit to clear
            pass
        return self.recv(*recv_args)

    def initialize(self):
        self._init_attributes = { 
                pyvisa.constants.VI_ATTR_TERMCHAR_EN: 1,
                pyvisa.constants.VI_ATTR_TMO_VALUE: 5000,   # Increase timeout
                pyvisa.constants.VI_ATTR_SEND_END_EN: 0}    # Do not terminate
                                                            # with EOI
        super().initialize()

    #  M1,CT0,T1,W2,SM0,L0,C0,D1,BUR 0001 #,PER 1.00 MS,DBL 200 US,
    # DEL 65.0 NS,DTY 50%,WID 100 US,LEE 10.0 NS,TRE 10.0 NS,HIL +1.00 V,
    # LOL +0.00 V,
    @Feat()
    def settings(self):
        return self.query('CST')

    @Feat(values=dict(normal='1', trigger='2', gate='3', external_width='4', 
        external_burst='5'), read_once=True)
    def trigger_mode(self):
        return re.match(r' *M([1-5]),', self.settings).group(1)

    @trigger_mode.setter
    def trigger_mode(self, value):
        self.send('M' + value)

    @Feat(values=dict(off='0', positive='1', negative='2', both='3'),
            read_once=True)
    def trigger_control(self):
        return re.search(r',T([0-3]),', self.settings).group(1)

    @trigger_control.setter
    def trigger_control(self, value):
        self.send('T' + value)

    @Feat(values={True: '1', False: '0'}, read_once=True)
    def complement(self):
        return re.search(r'.*,C([01]),', self.settings).group(1)

    @complement.setter
    def complement(self, value):
        self.send('C' + value)

    @Feat(values={True: '0', False: '1'}, read_once=True)
    def enable(self):
        return re.search(r'.*,D([01]),', self.settings).group(1)

    @enable.setter
    def enable(self, value):
        self.send('D' + value)

    @Action()
    def trigger(self):
        super().trigger()

    period = HP8112AFeat('PER', (Q_(20, 'ns'), Q_(950, 'ms')))
    delay = HP8112AFeat('DEL', (Q_(75, 'ns'), Q_(950, 'ms')))
    #DBL
    #DTY
    width = HP8112AFeat('WID', (Q_(10, 'ns'), Q_(950, 'ms')))
    leading_edge = HP8112AFeat('LEE', (Q_(6.5, 'ns'), Q_(95, 'ms')))
    trailing_edge = HP8112AFeat('TRE', (Q_(6.5, 'ns'), Q_(95, 'ms')))
    high_level = HP8112AFeat('HIL', (Q_(-7.9, 'V'), Q_(8, 'V')))
    low_level = HP8112AFeat('LOL', (Q_(-8, 'V'), Q_(7.9, 'V')))
    #BUR


if __name__ == '__main__':
    #inst = HP8112A('GPIB0::11::INSTR', library_path=r'C:\Archivos de programa\National Instruments\RT Images\NI-VISA\2.5.1\visa32.dll')
    #inst = HP8112A('GPIB0::11::INSTR', library_path=r'C:\Archivos de programa\VISA\winnt\agvisa\agbin\visa32.dll')
    #inst = HP8112A('GPIB0::11::INSTR', library_path='C:\\lantz\\system32\\visa32.dll')
    from lantz.log import log_to_screen, DEBUG
    log_to_screen(DEBUG)
    inst = HP8112A('GPIB0::11::INSTR')
    inst.initialize()
    start_test_app(inst)
    inst.finalize()
    print(inst.refresh())
