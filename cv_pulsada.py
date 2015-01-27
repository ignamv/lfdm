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
    def pulso_manual(self):
        # Para no pedirlo en medio del pulso
        leading, trailing = yield from self.gen.refresh_async(
                ['leading_edge', 'trailing_edge'])
        # Evito glitches configurando en este orden
        yield from self.gen.update_async(trigger_control = 'negative')
        yield from self.gen.update_async(trigger_mode = 'external_width')
        yield from self.gen.update_async(trigger_control = 'positive')
        yield from self.sleep(self._ancho)
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

if __name__ == '__main__':
    from hp8112a import HP8112A
    from gwinstekgds2062 import GwinstekGDS2062
    from lantz import initialize_many

    gen = HP8112A('GPIB0::11::INSTR')
    osc = GwinstekGDS2062('ASRL5::INSTR')
    initialize_many([gen, osc])
    cv = CV_Pulsada(gen, osc)
