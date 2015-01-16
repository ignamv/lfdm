import logging
import numpy as np

from lantz import initialize_many, finalize_many, LOGGER, Q_
from lantz.log import log_to_screen, DEBUG

from keithley220 import Keithley220
from keithley617 import Keithley617
from keithley705 import Keithley705

fh = logging.FileHandler('error.log')
fh.setLevel(logging.DEBUG)
LOGGER.addHandler(fh)

i_src = Keithley220('GPIB0::12::INSTR')
electrometro = Keithley617('GPIB0::28::INSTR')
matriz = Keithley705('GPIB0::29::INSTR')
instrumentos = (i_src, electrometro, matriz)

salida = open('salida.txt', 'w')

initialize_many(instrumentos)

matriz.channel[(2,1)] = True
matriz.channel[(4,3)] = True

i_src.current = Q_(2, 'nA')
i_src.voltage_limit = Q_(5, 'V')
i_src.output = True

puntos_por_decada = 2
corrientes = Q_(np.power(10, np.arange(puntos_por_decada*np.log10(2e-9),
    puntos_por_decada*np.log10(2e-3)+1) / puntos_por_decada), 'A')
tensiones = Q_(np.empty(len(corrientes)), 'V')
for ii, corriente in enumerate(corrientes):
    i_src.current = corriente
    tensiones[ii] = electrometro.stable_voltage()
    salida.write('{}\t{}\n'.format(corriente.to('A').magnitude,
        tensiones[ii].to('V').magnitude))

salida.close()

