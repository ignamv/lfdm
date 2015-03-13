from lantz import Q_
import time
import asyncio
import logging
import numpy as np

logger = logging.getLogger(__name__)

class CV_Pulsada(object):
    SETUP_SUBIDA = 1
    SETUP_BAJADA = 2

    # Máximo ancho de pulso del generador
    generador_max = Q_(950, 'ms')

    def __init__(self, generador, osciloscopio):
        self.gen = generador
        self.gen.refresh()
        self.osc = osciloscopio
        self.osc.refresh()
        self.epsilon = .05

    @asyncio.coroutine
    def setAncho(self, ancho, capturar_subida=True, capturar_bajada=True):
        if not (capturar_subida or capturar_bajada):
            raise Exception('No se pidió un flanco para capturar')
        leading, trailing = yield from self.gen.refresh_async(
                ['leading_edge', 'trailing_edge'])
        self.manual = ancho > self.generador_max
        if self.manual:
            yield from self.gen.update_async(trigger_mode = 'external_width')
        else:
            yield from self.gen.update_async(width = ancho,
                    trigger_mode = 'trigger')
        settings = None
        if capturar_subida and capturar_bajada and not self.manual:
            # Configurar osciloscopio para capturar todo
            # Sin RUN actualiza el zoom en vez de la escala de adquisición
            settings = dict(delay = .5 * ancho, time_scale = 
                    self.osc.fit_time(ancho + .5 * (leading + trailing)))
        else:
            settings = dict(delay=Q_(0, 's'),
                    time_scale = self.osc.fit_time(leading))
            if capturar_subida:
                settings['trigger_slope'] = 'rising'
            else:
                settings['trigger_slope'] = 'falling'
        # Sin RUN actualiza el zoom en vez de la escala de adquisición
        yield from self.osc.run_async()
        yield from self.osc.update_async(settings)
        self._ancho = ancho
        self.capturar_bajada = capturar_bajada
        self.capturar_subida = capturar_subida

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
        yield from self.osc.run_async()
        yield from self.osc.update_async(trigger_mode='single',
                trigger_level = avg,
                trigger_slope='rising', trigger_source=1, 
                trigger_couple='dc', trigger_type='edge', 
                record_length=1, voltage_scale={1: self.osc.fit_voltage(span)},
                offset={1: -avg}, invert = {2: False})
        yield from self.osc.stop_async()
        yield from self.sleep(Q_(0.1, 's'))

    @asyncio.coroutine
    def pulso_manual(self):
        flancos = []
        leading = self.gen.recall('leading_edge')
        trailing = self.gen.recall('trailing_edge')
        #yield from self.osc.recall_setup_async(self.SETUP_SUBIDA)
        # Evito glitches configurando en este orden
        beginning = time.time()
        yield from self.gen.update_async(trigger_control = 'positive')
        yield from self.sleep(self.osc.xdivisions *
                self.osc.recall('time_scale') + Q_(0, 'ms'))
        # El instrumento interpreta el ancho como ancho altura mitad
        # Imito este comportamiento
        if self.capturar_subida:
            subida_raw = yield from self.osc.acquire_async([1,2], False)
        #yield from self.osc.recall_setup_async(self.SETUP_BAJADA)
        yield from self.osc.update_async(trigger_slope='falling',
                invert = { 2: True})
        yield from self.osc.run_async()
        delay = self._ancho + .5 * (leading - trailing) - Q_(time.time() 
                - beginning, 's')
        if delay < Q_(0, 's'):
            print("Pulso demasiado ancho por {:.3e~}".format(-delay))
        else:
            yield from self.sleep(delay)
        yield from self.gen.update_async(trigger_control = 'negative')
        yield from self.sleep(self.osc.xdivisions *
                self.osc.recall('time_scale') + Q_(0, 'ms'))
        if self.capturar_bajada:
            bajada = yield from self.osc.acquire_async([1,2])
            flancos.append(bajada)
        yield from self.osc.update_async(trigger_slope='rising', 
                invert = {2: False})
        if self.capturar_subida:
            flancos.insert(0, self.osc.process_data(subida_raw))
        return flancos

    @asyncio.coroutine
    def pulso_normal(self):
        # Para no pedirlo en medio del pulso
        leading, trailing, width = yield from self.gen.refresh_async(
                ['leading_edge', 'trailing_edge', 'width'])
        yield from self.sleep(.5 * self.osc.recall('time_scale') *
                self.osc.xdivisions - self.osc.recall('delay') + Q_(200, 'ms'))
        yield from self.gen.trigger_async()
        yield from self.sleep(self.osc.xdivisions *
                self.osc.recall('time_scale'))
        pulso = yield from self.osc.acquire_async([1,2])
        return (pulso,)

    @asyncio.coroutine
    def sleep(self, interval):
        yield from asyncio.sleep(Q_(interval).to('s').magnitude)

@asyncio.coroutine
def prueba(cv):
    yield from cv.setAncho(Q_(1, 's'))
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
    yield from cv.configurar()
    yield from cv.setAncho(Q_(.1, 's'))
    yield from cv.gen.update_async(enable=True)
    from matplotlib import pyplot as plt
    plt.figure(figsize=(9,9))
    plots = 8
    filas = int(np.round(np.sqrt(plots)))
    columnas = int(np.ceil(plots / filas))
    for fig in range(1, plots + 1):
        plt.subplot(filas, columnas, fig)
        yield from cv.sleep(Q_(.5, 's'))
        print('Mandando pulso...', end='', flush=True)
        pulso = yield from cv.pulso()
        print('listo')
        plt.plot(pulso[0][1])
    plt.savefig('cv.png')

@asyncio.coroutine
def prueba3(cv):
    yield from cv.configurar()
    yield from cv.gen.update_async(enable=True)
    from matplotlib import pyplot as plt
    plt.figure(figsize=(9,9))
    plots = 16
    filas = int(np.round(np.sqrt(plots)))
    columnas = int(np.ceil(plots / filas))
    yield from cv.setAncho(Q_(.1, 's'))
    for ii, tt in enumerate(np.power(10, np.linspace(np.log10(200e-6),
                                                     np.log10(200e-3), 16))):
        plt.subplot(filas, columnas, ii + 1)
        print('config...', end='', flush=True)
        capturar_bajada = ii < 6
        yield from cv.setAncho(Q_(tt, 's'), True, capturar_bajada)
        print('pausa...', end='', flush=True)
        yield from cv.sleep(Q_(1, 's'))
        print('pulso...', end='', flush=True)
        pulso = yield from cv.pulso()
        print('listo')
        plt.plot(pulso[0][1])
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
    fut = asyncio.async(prueba3(cv))
    asyncio.get_event_loop().run_until_complete(fut)
