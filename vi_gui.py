import asyncio
import numpy as np

from enum import Enum
from lantz import Q_
from lantz.log import log_to_screen
import logging
from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt4.QtCore import pyqtSlot
from PyQt4.uic import loadUiType
from qtdebug import set_trace
from taskwrap import taskwrap

from lantzinitializedialog import LantzInitializeDialog
from keithley220 import Keithley220
from keithley617 import Keithley617
from keithley705 import Keithley705

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

form, base = loadUiType('vi.ui')

class VI_GUI(base):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = form()
        self.ui.setupUi(self)
        # Set up grafico
        self.figure = Figure(frameon=False)
        self.axes = self.figure.add_axes((.1,.1,.85,.85), xscale='log',
                yscale='log')
        self.axes.set_xlim((1e-10, 1e-2))
        self.axes.set_ylim((1e-6, 1e1))
        self.axes.hold(True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setMinimumSize(320, 240)
        self.ui.layout_grafico.addWidget(self.canvas)
        self.ui.layout_grafico.addWidget(NavigationToolbar2QT(self.canvas,
            self))
        # Conectar a instrumentos
        self.i_src = Keithley220('GPIB0::12::INSTR')
        self.i_src.initialize()
        self.electrometro = Keithley617('GPIB0::28::INSTR')
        self.electrometro.initialize()
        self.matriz = Keithley705('GPIB0::29::INSTR')
        self.matriz.initialize()

        self.setMidiendo(False)
        self.ui.empezar.clicked.connect(self.on_empezar_clicked)

    @pyqtSlot(bool)
    def on_lineal_toggled(self, state):
        self.ui.incremento.setEnabled(state)

    @pyqtSlot(bool)
    def on_geometrico_toggled(self, state):
        self.ui.puntos_por_decada.setEnabled(state)

    escalas = ['linear', 'log']
    @pyqtSlot(bool)
    def on_xlog_toggled(self, state):
        self.axes.set_xscale(self.escalas[state])
        self.canvas.draw()
    @pyqtSlot(bool)
    def on_ylog_toggled(self, state):
        self.axes.set_yscale(self.escalas[state])
        self.canvas.draw()

    class Estado(Enum):
        idle = 0
        correr = 1

    @asyncio.coroutine
    def medir(self):
        self.setMidiendo(True)
        yield from self.matriz.close_async((2, 1))
        yield from self.matriz.close_async((4, 3))
        yield from self.electrometro.update_async(zero_check = False)
        yield from self.i_src.update_async(
            current=Q_(self.corrientes[0], 'A'),
            voltage_limit = Q_(5, 'V'),
            output = True)
        for corriente in self.corrientes:
            logger.info('Corriente nueva: %f A',corriente)
            tension = corriente * 1e3
            logger.info('Tensión nueva: %f A', tension)
            logger.debug(self.puntos)
            logger.debug(self.corrientes)
            logger.debug(self.tensiones)
            self.tensiones[self.puntos] = tension
            self.plot.set_xdata(self.corrientes[:self.puntos])
            self.plot.set_ydata(self.tensiones[:self.puntos])
            self.puntos += 1
            self.canvas.draw()

    @asyncio.coroutine
    def terminar(self):
        yield from self.i_src.update_async(dict(
            current = Q_(0, 'A'),
            output = False))
        yield from self.electrometro.update_async(dict(zero_check = True))
        yield from self.matriz.reset_async()
        self.setMidiendo(False)

    def setMidiendo(self, midiendo):
        self.midiendo = midiendo
        self.ui.parametros.setEnabled(not midiendo)
        self.ui.terminar.setEnabled(midiendo)

    @pyqtSlot()
    @taskwrap
    def on_empezar_clicked(self):
        logger.debug('Empezar')
        corriente_inicial = Q_(self.ui.corriente_inicial.text())\
                .to('A').magnitude
        corriente_final = Q_(self.ui.corriente_final.text())\
                .to('A').magnitude
        if self.ui.lineal.isChecked():
            incremento = Q_(self.ui.incremento.text()).to('A').magnitude
            self.corrientes = np.arange(corriente_inicial, corriente_final,
                    incremento)
        else:
            puntos_por_decada = int(self.ui.puntos_por_decada.text())
            self.corrientes = np.power(10, np.arange(
                np.log10(corriente_inicial), np.log10(corriente_final),
                1. / puntos_por_decada))
        self.tensiones = np.empty(len(self.corrientes))
        self.puntos = 0
        self.plot, = self.axes.plot([], [], 'x', label='Hola')
        try:
            yield from self.medir()
        finally:
            yield from self.terminar()

if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication
    from quamash import QEventLoop
    log_to_screen(logging.DEBUG)
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop) 
    ui = VI_GUI()
    ui.show()
    exit(loop.run_forever())
