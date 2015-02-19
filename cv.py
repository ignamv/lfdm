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
              (3, 4),
              (5, 1)]
for canal in conexiones:
    matriz.close(canal)
matriz.execute()

# Configuro el LCR
lcr.equivalent_circuit = 'parallel'
lcr.frequency = Q_(1, 'MHz')
lcr.drive_level = Q_(2, 'mV')

archivo = r'..\mediciones\vi_silicio\cv {}.raw'.format(datetime.today().strftime( '%Y-%m-%d_%H.%M.%S'))
salida_raw = open(archivo, 'w', encoding='utf-8')
print('Salida raw: ' + archivo)
archivo = r'..\mediciones\vi_silicio\cv {}.txt'.format(datetime.today().strftime( '%Y-%m-%d_%H.%M.%S'))
salida = open(archivo, 'w', encoding='utf-8')
print('Salida linda: ' + archivo)
salida_raw.write('# {}\n'.format(' '.join(sys.argv)))
salida_raw.write('# Bias: ' + bias_source.learn_raw + '\n')
salida_raw.write('# Bias: ' + bias_source.learn_raw + '\n')
salida_raw.write('# LCR: {} {} {}\n'.format(lcr.recall('equivalent_circuit'),
    lcr.recall('frequency'), lcr.recall('drive_level')))
salida_raw.write('# Matriz: {}\n'.format(matriz.status))
tensiones = Q_(np.linspace(-1., 1., 40), 'V')

salida_raw.write('# Tensión [V]\tC [F]\tR [ohm]\n')
salida.write('# Tensión [V]\tC [F]\tsigmaC[F]\tR [ohm]\tsigmaR[ohm]\n')
bias_source.bias_voltage = tensiones[0]
sleep(1)
repeticiones_max = 10
mediciones = np.empty((repeticiones_max, 2))
for ii, bias in enumerate(tensiones):
    print('{}/{}'.format(ii + 1, len(tensiones)), end='', flush=True)
    bias_source.bias_voltage = bias
    mediciones[0, :] = lcr.measure
    for jj in range(1, repeticiones_max):
        salida_raw.write('{}\t{}\t{}\n'.format(
            bias.magnitude, mediciones[jj - 1, 0], mediciones[jj - 1, 1]))
        mediciones[jj, :] = lcr.measure
        c, r = lcr.measure
        if np.linalg.norm(mediciones[jj,:]-mediciones[jj-1,:]) \
                / np.linalg.norm(mediciones[jj,:]) < .1:
            break
        print('.', end='', flush=True)
    salida.write('{}\t{}\t{}\t{}\t{}\n'.format(
        bias.magnitude, np.mean(mediciones[:jj+1,0]), 
        np.std(mediciones[:jj+1,0]), np.mean(mediciones[:jj+1,1]), 
        np.std(mediciones[:jj+1,1])))
    print('')
bias_source.bias_voltage = Q_(0, 'V')

matriz.reset()
