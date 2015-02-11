# encoding: utf-8
from lantz import Q_
import numpy as np
import sys
from time import sleep
from datetime import datetime

from keithley705 import Keithley705
from gwinsteklcr8110g import GwinstekLCR8110G
from hp4277a import HP4277A

# Me conecto a los instrumentos
matriz = Keithley705('GPIB0::29::INSTR')
matriz.initialize()

lcr = GwinstekLCR8110G(port=0, timeout=5)
lcr.initialize()

bias_source = HP4277A('GPIB0::17::INSTR')
bias_source.initialize()

# Configuro la matriz
matriz.matrix_mode()
matriz.reset()
conexiones = [(3, 2),
              (3, 3),
              (5, 1)]
for canal in conexiones:
    matriz.close(canal)
matriz.execute()

# Configuro el LCR
lcr.equivalent_circuit = 'parallel'
lcr.frequency = Q_(1, 'MHz')
lcr.drive_level = Q_(100, 'mV')

archivo = r'..\mediciones\{}.txt'.format(datetime.today().strftime(
    '%Y-%m-%d_%H.%M.%S'))
salida = open(archivo, 'w', encoding='utf-8')
print('Escribiendo a ' + archivo)
salida.write('# {}\n'.format(' '.join(sys.argv)))
salida.write('# Bias: ' + bias_source.learn_raw + '\n')
salida.write('# Bias: ' + bias_source.learn_raw + '\n')
salida.write('# LCR: {} {} {}\n'.format(lcr.recall('equivalent_circuit'),
    lcr.recall('frequency'), lcr.recall('drive_level')))
salida.write('# Matriz: {}\n'.format(matriz.status))
tensiones = Q_(np.linspace(-3, 1, 40), 'V')

salida.write('# Tensión [V]\tC [F]\tR [ohm]\n')
bias_source.bias_voltage = tensiones[0]
sleep(1)
for ii, bias in enumerate(tensiones):
    print('{}/{}'.format(ii + 1, len(tensiones)), end='', flush=True)
    bias_source.bias_voltage = bias
    c, r = lcr.measure_stable(.05)
    salida.write('{}\t{}\t{}\n'.format(
        bias.magnitude, c, r))
    print('')
bias_source.bias_voltage = Q_(0, 'V')

matriz.reset()
