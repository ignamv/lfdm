import keithleydataacq
from time import sleep

device = keithleydataacq.DtDevice.open_first()
device.da[0].continuousDataFlow = False
device.da[0].configure()

for ii in range(6):
    device.da[0].write(0, ii, 1)
    sleep(.7)
