from lantz import Q_
from time import sleep
import asyncio
import keithleydataacq

device = keithleydataacq.DtDevice.open_first()
device.dout[0].continuousDataFlow = False
device.dout[0].configure()

for ii in range(6):
    device.dout[0].write(0, ii, 1)
    sleep(.7)
