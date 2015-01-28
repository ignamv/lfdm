import asyncio
import traceback
import taskwrap
import sys
import numpy as np
import logging
import os

from enum import Enum
from lantz import Q_
from lantz.log import log_to_screen
from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PyQt4.QtCore import pyqtSlot, QObject
from PyQt4.uic import loadUiType
from qtdebug import set_trace

from lantzinitializedialog import LantzInitializeDialog
from savesettings import SaveSettings
from autoincrement_file import get_save_filename
from keithley220 import Keithley220
from keithley617 import Keithley617
from keithley705 import Keithley705

logger = logging.getLogger(__name__)

form, base = loadUiType('vi.ui')

class VI_GUI(base):
    savesettings = [
            ('corriente_inicial', 'text'),
            ('corriente_final', 'text'),
            ('incremento', 'text'),
            ('puntos_por_decada', 'text'),
            ('lineal', 'checked'),
            ('geometrico', 'checked'),
            ('xlog', 'checked'),
            ('ylog', 'checked'),
            ]
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
        self.electrometro = Keithley617('GPIB0::28::INSTR')
        self.matriz = Keithley705('GPIB0::29::INSTR')
        self.instruments = [self.i_src, self.matriz, self.electrometro]
        init = LantzInitializeDialog(self.instruments, parent=self)
        init.show()

        self.setMidiendo(False)
        SaveSettings(self.savesettings, self)

    def closeEvent(self, event):
        # TODO: interrupt measurement
        if self.midiendo:
            event.ignore()
            return
        init = LantzInitializeDialog(self.instruments, parent=self,
                finalize=True)
        init.show()
        return super().closeEvent(event)

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
        yield from self.electrometro.update_async(zero_check = False,
                zero_correct = False)
        yield from self.i_src.update_async(
            current=self.corrientes[0],
            voltage_limit = Q_(5, 'V'),
            output = True)
        # Stabilize output
        yield from asyncio.sleep(.5)
        for ii, corriente in enumerate(self.corrientes):
            #yield from self.i_src.update_async(current=corriente)
            logger.debug('Corriente %d/%d: %s', ii + 1, len(self.corrientes),
                    corriente)
            #tension = yield from self.electrometro.refresh_async('voltage')
            tension = corriente * Q_(1.034, 'kohm')
            logger.debug('Tensión: %s', tension)
            self.tensiones[ii] = tension
            self.plot.set_xdata(self.corrientes[:ii].magnitude)
            self.plot.set_ydata(self.tensiones[:ii].magnitude)
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
    @taskwrap.taskwrap
    def on_empezar_clicked(self):
        logger.debug('Empezar')
        corriente_inicial = Q_(self.ui.corriente_inicial.text())\
                .to('A').magnitude
        corriente_final = Q_(self.ui.corriente_final.text())\
                .to('A').magnitude
        if self.ui.lineal.isChecked():
            incremento = Q_(self.ui.incremento.text()).to('A').magnitude
            self.corrientes = Q_(np.arange(corriente_inicial, corriente_final,
                    incremento), 'A')
        else:
            puntos_por_decada = int(self.ui.puntos_por_decada.text())
            self.corrientes = Q_(np.power(10, np.arange(
                np.log10(corriente_inicial), np.log10(corriente_final) + 
                1.5 / puntos_por_decada, 1. / puntos_por_decada)), 'A')
        logger.debug('Voy a medir corrientes %s', self.corrientes)
        self.tensiones = Q_(np.empty(len(self.corrientes)), 'V')
        self.plot, = self.axes.plot([], [], 'x', label='Hola')
        try:
            yield from self.medir()
        except Exception as e:
            logger.error(''.join(traceback.format_exception(*sys.exc_info())))
        finally:
            yield from self.terminar()
        filename = get_save_filename(self, caption='Guardar medición',
                filter='*.txt;;*.*')
        if filename == '':
            return
        fd = open(filename, 'w', encoding='utf8')
        fd.write('# Corriente inicial: {:e}A\n'.format(corriente_inicial))
        fd.write('# Corriente final: {:e}A\n'.format(corriente_final))
        if self.ui.lineal.isChecked():
            fd.write('# Incremento: {:e}A\n'.format(incremento))
        else:
            fd.write('# {} puntos por decada\n'.format(puntos_por_decada))
        fd.write('# Corriente[A]\tTension[V]')
        for ii in range(len(self.corrientes)):
            fd.write('{:e}\t{:e}\n'.format(self.corrientes[ii].magnitude,
                self.tensiones[ii].magnitude))
        fd.close()


if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QCoreApplication
    QCoreApplication.setOrganizationName('LFDM')
    QCoreApplication.setApplicationName('VI_GUI')
    from quamash import QEventLoop
    consola = logging.StreamHandler()
    consola.setLevel(logging.DEBUG)
    logger.addHandler(consola)
    logging.basicConfig(level=logging.DEBUG, filename='error.log', mode='w')
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop) 
    ui = VI_GUI()
    ui.show()
    exit(loop.run_forever())
