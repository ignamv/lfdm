
from lantz import Q_
import numpy as np
from gwinsteklcr8110g import GwinstekLCR8110G
from hp4277a import HP4277A
#lcr = GwinstekLCR8110G(port=0, timeout=5)
lcr = HP4277A('GPIB0::17::INSTR')
lcr.initialize()

#lcr.equivalent_circuit = 'series'

puntos_por_decada = 5
frecuencias = np.power(10, np.arange(4, 6, 1./puntos_por_decada))
print('#F [Hz]\tC[F]\tR[Ohm]')
for frecuencia in frecuencias:
    lcr.frequency(Q_(frecuencia, 'Hz'))
    try:
        c, r = lcr.measure_stable()
    except:
        continue
    print('{}\t{}\t{}'.format(frecuencia, c, r))

lcr.finalize()
