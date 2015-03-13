"""Tira pulsos con el generador y los captura con el osciloscopio en modo
single.
Varía el delay entre "RUN" y pulso, y entre pulso y ACQUIRE
Luego informa cuántas adquisiciones salieron bien (no llenas de ceros)"""
from hp8112a import HP8112A
from gwinstekgds2062 import GwinstekGDS2062
import lantz
from lantz import Q_
import logging
import time
import numpy as np

logger = logging.getLogger(__name__)

lantzlog = logging.FileHandler('lantz.log', mode='w')
lantz.LOGGER.setLevel(logging.DEBUG)
lantz.LOGGER.addHandler(lantzlog)

consola = logging.StreamHandler()
consola.setLevel(logging.DEBUG)
logger.addHandler(consola)

gen = HP8112A('GPIB0::11::INSTR')
osc = GwinstekGDS2062('ASRL5::INSTR')
lantz.initialize_many([gen, osc])

tension = Q_(2, 'V')
ancho = Q_(1, 'ms')

def medir_pulso(pausa_antes, pausa_despues):
    osc.run()
    time.sleep(pausa_antes)
    gen.trigger()
    if pausa_despues != 0:
        time.sleep(pausa_despues)
    datos = osc.acquire([1])
    # Si no funcionó devuelve todos 0
    return np.any(datos[1])
    
pruebas = 20
print(sum(medir_pulso(.05,0) for ii in range(pruebas)))
