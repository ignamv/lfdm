import keithleydataacq
from lantz import Q_

device = keithleydataacq.DtDevice.open_first()
device.ct[0].clockFrequency = Q_(200, 'Hz')
device.ct[0].mode = 'ONESHOT'
#device.ct[0].pulseWidth = 50.
device.ct[0].configure()
device.ct[0].start()
