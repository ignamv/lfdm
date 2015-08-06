# encoding: utf-8
import argparse
import numpy as np
import sys
from time import sleep
from datetime import datetime

from lantz import Q_
from keithley705 import Keithley705
from gwinsteklcr8110g import GwinstekLCR8110G
from hp4277a import HP4277A
from util import linspace, arange

parser = argparse.ArgumentParser()
parser.add_argument('salida')
parser.add_argument('--volver', help='Medir ida y vuelta',
    action='store_true')
parser.add_argument('--vinicial', type=Q_, help='Tensión inicial',
        required=True)
parser.add_argument('--vfinal', type=Q_, help='Tensión final', required=True)
parser.add_argument('--frecuencia', type=Q_, help='Frecuencia del LCR',
        default=Q_(995, 'kHz'))
parser.add_argument('--pausa', type=Q_, default=Q_(10, 'ms'),
        help='Pausa entre cambio de bias y medición')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--vpaso', type=Q_, help='Aumento de tensión entre pasos')
group.add_argument('--pasos', type=int, help='Cantidad de pasos')
args = parser.parse_args()

# Me conecto a los instrumentos
matriz = Keithley705('GPIB0::29::INSTR')
matriz.initialize()

lcr = GwinstekLCR8110G(port=0, timeout=5)
lcr.initialize()
lcr.drive_level = Q_(20, 'mV')

bias_source = HP4277A('GPIB0::17::INSTR')
bias_source.initialize()
#lcr = bias_source
#lcr.drive_level = 'low'

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
lcr.frequency = args.frecuencia

salida = open(args.salida, 'w', encoding='utf-8')
print('Salida: ' + args.salida)
salida.write('# {}\n'.format(' '.join(sys.argv)))
salida.write('# Bias: ' + bias_source.learn_raw + '\n')
salida.write('# Bias: ' + bias_source.learn_raw + '\n')
salida.write('# LCR: {} {} {}\n'.format(lcr.recall('equivalent_circuit'),
    lcr.recall('frequency'), lcr.recall('drive_level')))
salida.write('# Matriz: {}\n'.format(matriz.status))
if args.vpaso:
    tensiones = arange(args.vinicial, args.vfinal, args.vpaso).to('V')
else:
    tensiones = linspace(args.vinicial, args.vfinal, args.pasos).to('V')
if args.volver:
    tensiones = Q_(np.concatenate((tensiones, tensiones[::-1])), 'V')

salida.write('# Tensión [V]\tC [F]\tR [ohm]\tTiempo[s]\n')
try:
    bias_source.bias_voltage = tensiones[0]
    sleep(1)
    for ii, bias in enumerate(tensiones):
        print('{}/{}: {}'.format(ii + 1, len(tensiones), bias), end='', 
                flush=True)
        print('bias...', end='', flush=True)
        bias_source.bias_voltage = bias
        print('pause...', end='', flush=True)
        sleep(args.pausa.to('s').magnitude)
        print('medir...', end='', flush=True)
        c, r = lcr.measure
        print('escribir...', end='', flush=True)
        salida.write('{}\t{}\t{}\t{}\n'.format(bias.magnitude, c, r,
            datetime.now().timestamp()))
        print('')
finally:
    bias_source.bias_voltage = Q_(0, 'V')
    matriz.reset()
