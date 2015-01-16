# encoding: utf-8
from lantz import Q_
import numpy as np
from time import sleep
from datetime import datetime

from keithley705 import Keithley705
from gwinsteklcr8110g import GwinstekLCR8110G
from hp4277a import HP4277A

# Me conecto a los instrumentos
scanner = Keithley705('GPIB0::29::INSTR')
scanner.initialize()

lcr = GwinstekLCR8110G(port=0, timeout=5)
lcr.initialize()

bias_source = HP4277A('GPIB0::17::INSTR')
bias_source.initialize()

# Configuro la matriz
scanner.matrix_mode()
scanner.reset()
conexiones = [(3, 2),
              (3, 3),
              (5, 1)]
for columna, fila in conexiones:
    scanner.close_channel(columna, fila)
scanner.execute()

# Configuro el LCR
lcr.equivalent_circuit = 'parallel'
lcr.frequency = Q_(1, 'MHz')
lcr.drive_level = Q_(100, 'mV')

salida = open('mediciones\{}.txt'.format(datetime.today().strftime(
    '%Y-%m-%d_%H.%M.%S')), 'w')
salida.write('# Bias [V]\tC [F]\tRpar [Ohm]\n')
voltajes = Q_(np.linspace(-5, 10, 60), 'V')

bias_source.bias_voltage(voltajes[0])
sleep(1)
intentos = 20
for bias in voltajes:
    bias_source.bias_voltage(bias)
    c, r = lcr.measure
    for ii in range(intentos):
        c2, r2 = lcr.measure
        if ((c2 - c) / min(c, c2)).to("").magnitude < 1e-2:
            break
        c, r = c2, r2
        if ii == intentos - 1:
            raise Exception("Medición no converge")
    r = .5 * (r + r2)
    c = .5 * (c + c2)
    print(ii)
    salida.write('{}\t{}\t{}\n'.format(
        bias.magnitude, c.magnitude, r.magnitude))
