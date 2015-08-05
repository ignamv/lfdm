import logging
import argparse
import numpy as np
from time import sleep
from datetime import datetime

from lantz import initialize_many, finalize_many, LOGGER, Q_
from lantz.log import log_to_screen, DEBUG

from keithley220 import Keithley220
from keithley617 import Keithley617
from keithley705 import Keithley705
from util import arange, logspace

fh = logging.FileHandler('C:\lantz\error.log')
fh.setLevel(logging.DEBUG)
LOGGER.addHandler(fh)

parser = argparse.ArgumentParser()
parser.add_argument('salida')
parser.add_argument('--negativo', action='store_true',
        help='Invertir polaridad')
parser.add_argument('--invertir', action='store_true',
        help='Invertir orden (medir de mayor a menor corriente)')
parser.add_argument('--volver', action='store_true',
        help='Volver')
parser.add_argument('--no-estabilizar', action='store_true',
        help='No repetir medición de tensión')
#parser.add_argument('--estabilizar-imax', type=Q_, default=Q_(0,'A'),
        #help='Estabilizar por debajo de esta corriente')
parser.add_argument('--imin', type=Q_, help='Corriente mínima', required=True)
parser.add_argument('--imax', type=Q_, help='Corriente máxima', required=True)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--ipaso', type=Q_, help='Aumento de corriente entre pasos')
group.add_argument('--puntosdecada', type=int, help='Puntos por década')
parser.add_argument('--vlimite', type=Q_, help='Límite de tensión',
        required=True)
parser.add_argument('--delay', type=Q_, default=Q_(.1, 's'), 
        help='Tiempo entre cambio de corriente y medición')
parser.add_argument('--saltear', type=int, default=0,
        help='Saltear N mediciones al comienzo')
parser.add_argument('--estres', type=Q_, default=Q_(0, 's'),
        help='Tiempo de estrés en última corriente')
parser.add_argument('--muestreoestres', type=Q_, default=Q_(1, 's'),
        help='Tiempo entre mediciones de tensión durante estrés')
args = parser.parse_args()

i_src = Keithley220('GPIB0::12::INSTR')
electrometro = Keithley617('GPIB0::28::INSTR')
matriz = Keithley705('GPIB0::29::INSTR')
instrumentos = (i_src, electrometro, matriz)

salida = open(args.salida, 'w', encoding='utf-8')
salida.write('# Corriente inicial: {:e~}\n'.format(args.imin))
salida.write('# Corriente final: {:e~}\n'.format(args.imax))

initialize_many(instrumentos)

i_src.current = args.imin
i_src.voltage_limit = args.vlimite
electrometro.zero_check = False

if args.puntosdecada:
    corrientes = logspace(args.imin, args.imax, args.puntosdecada).to('A')
    salida.write('# {} puntos por decada\n'.format(args.puntosdecada))
else:
    corrientes = arange(args.imin, args.imax, args.ipaso).to('A')
    salida.write('# Paso {:e~}\n'.format(args.ipaso))
if args.negativo:
    corrientes = -corrientes
    salida.write('# Invierto polaridad\n')
if args.invertir:
    corrientes = corrientes[::-1]
    salida.write('# Invierto orden\n')
if args.volver:
    corrientes = Q_(np.concatenate((corrientes, corrientes[::-1])), 'A')
    salida.write('# Mido ida y vuelta\n')
if args.saltear != 0:
    corrientes = corrientes[args.saltear:]
    salida.write('# Salteo {} mediciones\n'.format(args.saltear))
salida.write('# Electrómetro: ' + electrometro.status + '\n')
salida.write('# Fuente de corriente: ' + i_src.status + '\n')
salida.write('# Matriz : ' + matriz.status + '\n')
salida.write('# Estrés : {:f~}\n'.format(args.estres))
salida.write('# Corriente[A]\tTension[V]\tTiempo[s]\n')
try:
    for channel in [(1, 1), (1, 4), (4, 2), (4, 3), (4, 4), (2, 1)]:
        matriz.close(channel)
    i_src.current = corrientes[0]
    i_src.output = True
    # Abro el corto a la salida de la fuente
    matriz.open((1, 1))
    sleep(.9)
    for ii, corriente in enumerate(corrientes):
        print('{}/{}: {:.1e~}'.format(ii+1, len(corrientes), corriente),
                end='', flush=True)
        i_src.current = corriente
        if args.no_estabilizar:
            sleep(args.delay.to('s').magnitude)
            tension = electrometro.voltage
            print(' {:.1e~}'.format(tension))
        else:
            tension, mediciones = electrometro.stable_voltage(.001)
            print(' {:.1e~} ({} mediciones)'.format(tension, mediciones))
        salida.write('{}\t{}\t{}\n'.format(corriente.to('A').magnitude,
            tension.to('V').magnitude, datetime.now().timestamp()))
        if ii == len(corrientes) - 1:
            print('Estresando {:f}'.format(args.estres))
            while args.estres > Q_(0, 's'):
                if args.estres >= args.muestreoestres:
                    ss = args.muestreoestres
                else:
                    ss = args.estres
                sleep(ss.to('s').magnitude)
                args.estres -= ss
                tension = electrometro.voltage
                salida.write('{}\t{}\t{}\n'.format(corriente.to('A').magnitude,
                    tension.to('V').magnitude, datetime.now().timestamp()))
finally:
    i_src.voltage_limit = Q_(1, 'V')
    sleep(.2)
    i_src.output = False
    i_src.current = Q_(0, 'A')
    matriz.close((1, 1))
    electrometro.zero_check = True
    sleep(.1)
    matriz.reset()

