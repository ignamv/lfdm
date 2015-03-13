from gwinstekgds2062 import GwinstekGDS2062
import time
import numpy as np

inst = GwinstekGDS2062('ASRL5::INSTR')
inst.initialize()
inicio = time.time()
datos = inst.acquire([1, 2], False)
fin = time.time()
print(fin - inicio)

from matplotlib import pyplot as plt
raw = np.frombuffer(datos[0][8:], dtype='>h')
tension = inst.process_data(datos)[1].to('V').magnitude
tiempo = inst.process_data(datos)['time'].to('us').magnitude
plt.subplot(1,2,1)
plt.plot(tiempo, tension)
plt.ylabel('Tensión [V]')
plt.xlabel('Tiempo [us]')
plt.subplot(1,2,2)
plt.plot(tiempo, raw)
plt.xlabel('Tiempo [us]')
plt.ylim((0, 0x10000))
plt.show()
