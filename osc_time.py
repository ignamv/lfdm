"""Configura el osciloscopio y generador para osc_time_p.py """
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

gen.update(trigger_mode = 'trigger', width = Q_(200, 'ns'),
    leading_edge = Q_(50, 'ns'), trailing_edge = Q_(50, 'ns'),
    high_level = tension, low_level = -tension, enable = True)
osc.update(record_length = 1, mode = 'normal', display = {1: True, 2: False},
        offset = {1: Q_(0, 'V')}, voltage_scale = {1: Q_(2, 'V')},
        trigger_level = Q_(0, 'V'), trigger_mode = 'single',
        trigger_slope = 'rising', trigger_source = 1, trigger_type = 'edge',
        delay = Q_(0, 's'), time_scale = Q_(25, 'ns'))

def medir_pulso(pausa_antes, pausa_despues):
    osc.run()
    time.sleep(pausa_antes)
    gen.trigger()
    time.sleep(pausa_despues)
    datos = osc.acquire([1])
    # Si no funcionó devuelve todos 0
    return np.any(datos[1])
    
print(medir_pulso(.9, .9))
