from lantz import Q_
import time
import asyncio
import logging
import numpy as np

logger = logging.getLogger(__name__)

class CV_Pulsada(object):
    SETUP_SUBIDA = 1
    SETUP_BAJADA = 2

    def __init__(self, generador, osciloscopio):
        self.gen = generador
        self.gen.refresh()
        self.osc = osciloscopio
        self.osc.refresh()
        self.setAncho(Q_(1., 's'))
        self.epsilon = .05

    def setAncho(self, ancho):
        self._ancho = ancho
        if ancho < Q_(950, 'ms'):
            self.gen.update(width = ancho)
            self.manual = False
        else:
            self.manual = True

    def ancho(self):
        return self._ancho

    @asyncio.coroutine
    def pulso(self):
        """Genera un pulso de ancho configurable

        La perilla LEVEL del generador debe estar hacia el límite izquierdo"""
        if self.manual:
            ret = yield from self.pulso_manual()
        else:
            ret = yield from self.pulso_normal()
        return ret

    @asyncio.coroutine
    def configurar(self):
        yield from self.gen.refresh_async()
        yield from self.osc.refresh_async()
        high, low, leading, trailing = yield from self.gen.refresh_async(
                ['high_level', 'low_level', 'leading_edge', 'trailing_edge'])
        avg = high + low
        span = 2. * (high - low)
        yield from self.gen.update_async(trigger_control = 'negative')
        yield from self.osc.fit_time_async(leading)
        yield from self.osc.fit_voltage_async(span, 1)
        yield from self.osc.update_async(trigger_mode='single')
        yield from self.osc.stop_async()
        yield from self.osc.run_async()
        yield from self.osc.update_async(trigger_level = Q_(0, 'V'),
                trigger_slope='falling', trigger_source=1, 
                trigger_couple='dc', trigger_type='edge', 
                delay=Q_(0, 's'), record_length=1,
                offset={1: -avg})
        yield from self.osc.save_setup_async(self.SETUP_BAJADA)
        yield from self.osc.update_async(trigger_slope='rising')
        yield from self.osc.save_setup_async(self.SETUP_SUBIDA)
        yield from self.sleep(Q_(0.1, 's'))



    @asyncio.coroutine
    def pulso_manual(self):
        leading = self.gen.recall('leading_edge')
        trailing = self.gen.recall('trailing_edge')
        #yield from self.osc.recall_setup_async(self.SETUP_SUBIDA)
        # Evito glitches configurando en este orden
        yield from self.gen.update_async(trigger_mode = 'external_width')
        beginning = time.time()
        yield from self.gen.update_async(trigger_control = 'positive')
        yield from self.sleep(self.osc.xdivisions *
                self.osc.recall('time_scale') + Q_(0, 'ms'))
        # El instrumento interpreta el ancho como ancho altura mitad
        # Imito este comportamiento
        subida_raw = yield from self.osc.acquire_async([1], False)
        #yield from self.osc.recall_setup_async(self.SETUP_BAJADA)
        yield from self.osc.update_async(trigger_slope='falling')
        yield from self.osc.run_async()
        yield from self.sleep(self._ancho + .5 * (leading - trailing) 
                - Q_(time.time() - beginning, 's'))
        yield from self.gen.update_async(trigger_control = 'negative')
        yield from self.sleep(self.osc.xdivisions *
                self.osc.recall('time_scale') + Q_(0, 'ms'))
        bajada = yield from self.osc.acquire_async([1])
        yield from self.osc.update_async(trigger_slope='rising')
        yield from self.osc.run_async()
        subida = self.osc.process_data(subida_raw)
        return (subida, bajada)

    @asyncio.coroutine
    def pulso_normal(self):
        # Para no pedirlo en medio del pulso
        leading, trailing, width = yield from self.gen.refresh_async(
                ['leading_edge', 'trailing_edge', 'width'])
        yield from self.osc.fit_time_async(width + .5 * (leading + trailing))
        yield from self.osc.update_async(delay = .5 * width)
        yield from self.gen.update_async(trigger_mode = 'trigger')
        yield from self.gen.trigger_async()
        yield from self.sleep(self.osc.xdivisions *
                self.osc.recall('time_scale'))
        pulso = yield from self.osc.acquire_async([1])
        yield from self.osc.run_async()
        return pulso

    @asyncio.coroutine
    def sleep(self, interval):
        yield from asyncio.sleep(Q_(interval).to('s').magnitude)

@asyncio.coroutine
def prueba(cv):
    cv.setAncho(Q_(1, 's'))
    yield from cv.configurar()
    yield from cv.gen.update_async(enable=True)
    from matplotlib import pyplot as plt
    plt.figure(figsize=(9,9))
    for fig in range(1,17):
        plt.subplot(4,4,fig)
        yield from cv.sleep(Q_(.5, 's'))
        print('Mandando pulso...', end='', flush=True)
        subida, bajada = yield from cv.pulso()
        print('listo')
        plt.plot(subida[1], label='Subida')
        plt.plot(bajada[1], label='Bajada')
        plt.legend()
    plt.savefig('cv.png')

@asyncio.coroutine
def prueba2(cv):
    cv.setAncho(Q_(.1, 's'))
    yield from cv.configurar()
    yield from cv.gen.update_async(enable=True)
    yield from cv.osc.stop_async()
    yield from cv.osc.run_async()
    from matplotlib import pyplot as plt
    plt.figure(figsize=(9,9))
    plots = 4
    filas = int(np.round(np.sqrt(plots)))
    columnas = int(np.ceil(plots / filas))
    for fig in range(1, plots + 1):
        plt.subplot(filas, columnas, fig)
        yield from cv.sleep(Q_(.5, 's'))
        print('Mandando pulso...', end='', flush=True)
        pulso = yield from cv.pulso()
        print('listo')
        plt.plot(pulso[1])
    plt.savefig('cv.png')

if __name__ == '__main__':
    from hp8112a import HP8112A
    from gwinstekgds2062 import GwinstekGDS2062
    from lantz import initialize_many
    import lantz
    lantzlog = logging.FileHandler('lantz.log', mode='w')
    lantz.LOGGER.setLevel(logging.DEBUG)
    lantz.LOGGER.addHandler(lantzlog)
    consola = logging.StreamHandler()
    consola.setLevel(logging.DEBUG)
    logger.addHandler(consola)

    gen = HP8112A('GPIB0::11::INSTR')
    osc = GwinstekGDS2062('ASRL5::INSTR')
    initialize_many([gen, osc])
    cv = CV_Pulsada(gen, osc)
    fut = asyncio.async(prueba2(cv))
    asyncio.get_event_loop().run_until_complete(fut)
