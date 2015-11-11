import keithleydataacq
from lantz import Q_
from time import sleep
import asyncio
import scipy as sp

device = keithleydataacq.DtDevice.open_first()
device.ad[0].initialize()
device.ad[0].sampleRate = Q_(5000, 'Hz')
device.ad[0].differential = True
BUFFER_SIZE = 50000
device.ad[0].prepareBuffers(3, BUFFER_SIZE)
#device.ad[0].configure([(0, 1), (1, 1), (2, 1)])
device.ad[0].configure([(0, 1)])
device.ad[0].start()

fd = open('largo.txt', 'wb')
@asyncio.coroutine
def task():
    accumulated_time = 0
    for ii in range(3):
        data = yield from device.ad[0].read_async()
        data['time'] += accumulated_time
        accumulated_time += (data['time'][1] - data['time'][0]) * len(data['time'])
        sp.savetxt(fd, sp.column_stack((data['time'], data[0])))
        print('Read {}'.format(len(data)))
    print('Done')

asyncio.get_event_loop().run_until_complete(task())

