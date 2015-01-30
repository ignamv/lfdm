from lantz import Q_
from time import sleep
import asyncio

class CV_Pulsada(object):
    def __init__(self, generador, osciloscopio):
        self.gen = generador
        self.osc = osciloscopio
        self.setAncho(Q_(1., 's'))

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
            yield from self.pulso_manual()
        else:
            yield from self.pulso_normal()

    @asyncio.coroutine
    def configurar_osciloscopio(self):
        high, low, leading, trailing = yield from self.gen.refresh_async(
                ['high_level', 'low_level', 'leading_edge', 'trailing_edge'])
        time_scale = next(tt for tt in self.osc.time_scales 
                if tt > leading / 8.)
        yield from self.osc.update_async(trigger_level = high + low,
                trigger_slope='rising', trigger_source=1, 
                trigger_mode='single', trigger_couple='dc',
                trigger_type='edge', delay=Q_(0, 's'),
                time_scale=time_scale, record_length=0)


    @asyncio.coroutine
    def pulso_manual(self):
        # Para no pedirlo en medio del pulso
        leading, trailing = yield from self.gen.refresh_async(
                ['leading_edge', 'trailing_edge'])
        # Evito glitches configurando en este orden
        yield from self.gen.update_async(trigger_control = 'negative')
        yield from self.gen.update_async(trigger_mode = 'external_width')
        yield from self.gen.update_async(trigger_control = 'positive')
        # El instrumento interpreta el ancho como ancho altura mitad
        # Imito este comportamiento
        yield from self.sleep(.5 * self._ancho)
        self.osc.update_async(trigger_slope='falling')
        yield from self.sleep(.5 * self._ancho + .5 * (leading - trailing))
        yield from self.gen.update_async(trigger_control = 'negative')
        yield from self.sleep(trailing)

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
    cv.setAncho(Q_(2, 's'))
    yield from cv.configurar_osciloscopio()
    yield from asyncio.sleep(1)
    yield from cv.osc.run_async()
    yield from asyncio.sleep(.2)
    print('Mandando pulso')
    yield from cv.pulso()
    print('Listo')

if __name__ == '__main__':
    from hp8112a import HP8112A
    from gwinstekgds2062 import GwinstekGDS2062
    from lantz import initialize_many

    gen = HP8112A('GPIB0::11::INSTR')
    osc = GwinstekGDS2062('ASRL5::INSTR')
    initialize_many([gen, osc])
    cv = CV_Pulsada(gen, osc)
    fut = asyncio.async(prueba(cv))
    asyncio.get_event_loop().run_until_complete(fut)
