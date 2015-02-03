from lantz import Q_
import time
import asyncio
import logging

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
            self.gen.update_async(width = ancho)
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
        high, low, leading, trailing = yield from self.gen.refresh_async(
                ['high_level', 'low_level', 'leading_edge', 'trailing_edge'])
        trigger1 = 2. * (self.epsilon * high + (1 - self.epsilon) * low)
        trigger2 = 2. * (self.epsilon * low + (1 - self.epsilon) * high)
        time_scale = next(tt for tt in self.osc.time_scales 
                if tt >= leading / (self.osc.xdivisions - 2))
        print('time_scale={}'.format(time_scale))
        voltage_scale = next(vv for vv in self.osc.voltage_scales 
                if vv >= 2 * (high - low) / (self.osc.ydivisions - 2))
        print('voltage_scale={}'.format(voltage_scale))
        yield from self.osc.update_async(trigger_level = trigger2,
                trigger_slope='falling', trigger_source=1, 
                trigger_mode='single', trigger_couple='dc',
                trigger_type='edge', time_scale=time_scale,
                delay=trailing * (.5 - self.epsilon), record_length=0,
                offset={1: high + low}, voltage_scale={1: voltage_scale})
        yield from self.osc.save_setup_async(self.SETUP_BAJADA)
        yield from self.osc.update_async(trigger_slope='rising',
                trigger_level=trigger1, delay=leading * (.5 - self.epsilon))
        yield from self.osc.save_setup_async(self.SETUP_SUBIDA)

        yield from self.gen.update_async(trigger_control = 'negative')


    @asyncio.coroutine
    def pulso_manual(self):
        leading = self.gen.recall('leading_edge')
        trailing = self.gen.recall('trailing_edge')
        yield from self.osc.recall_setup_async(self.SETUP_SUBIDA)
        yield from self.osc.run_async()
        yield from self.sleep(Q_(.6875, 's'))
        # Evito glitches configurando en este orden
        yield from self.gen.update_async(trigger_mode = 'external_width')
        beginning = time.time()
        yield from self.gen.update_async(trigger_control = 'positive')
        # El instrumento interpreta el ancho como ancho altura mitad
        # Imito este comportamiento
        yield from self.sleep(self.osc.recall('time_scale') *
                self.osc.xdivisions + Q_(120, 'ms'))
        temp = yield from self.osc.acquire_async([1], False)
        yield from self.osc.recall_setup_async(self.SETUP_BAJADA)
        yield from self.osc.run_async()
        yield from self.sleep(self._ancho + .5 * (leading - trailing) 
                - Q_(time.time() - beginning, 's'))
        yield from self.gen.update_async(trigger_control = 'negative')
        yield from self.sleep(trailing)

        bajada = yield from self.osc.acquire_async([1])
        subida = self.osc.process_data(temp)
        return (subida, bajada)

    @asyncio.coroutine
    def pulso_normal(self):
        # Para no pedirlo en medio del pulso
        leading, trailing = yield from self.gen.refresh_async(
                ['leading_edge', 'trailing_edge'])
        yield from self.gen.update_async(trigger_mode = 'trigger')
        yield from self.gen.trigger_async()
        yield from self.sleep(leading + trailing + self._ancho)

    @asyncio.coroutine
    def sleep(self, interval):
        yield from asyncio.sleep(Q_(interval).to('s').magnitude)

@asyncio.coroutine
def prueba(cv):
    cv.setAncho(Q_(1, 's'))
    yield from cv.configurar()
    yield from cv.gen.update_async(enable=True)
    print('Mandando pulso')
    subida, bajada = yield from cv.pulso()
    from matplotlib import pyplot as plt
    plt.plot(subida[1], label='Subida')
    plt.plot(bajada[1], label='Bajada')
    plt.legend()
    plt.savefig('cv.png')
    print('Listo')

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
    fut = asyncio.async(prueba(cv))
    asyncio.get_event_loop().run_until_complete(fut)
