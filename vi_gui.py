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
from util import logspace, arange
from keithley220 import Keithley220
from keithley617 import Keithley617
from keithley705 import Keithley705
import tipiplot

logger = logging.getLogger(__name__)

form, base = loadUiType('vi.ui')

class VI_GUI(base):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = form()
        self.ui.setupUi(self)
        # Set up grafico
        self.plot = tipiplot.TipiPlot(self)
        self.plot.axes.set_xlim((1e-10, 1e-2))
        self.plot.axes.set_ylim((1e-6, 1e1))
        self.ui.layout_grafico.addWidget(self.plot)
        self.ui.xlog.toggled.connect(self.plot.setLogscaleX)
        self.ui.xlog.toggled.connect(self.plot.draw)
        self.ui.ylog.toggled.connect(self.plot.setLogscaleY)
        self.ui.ylog.toggled.connect(self.plot.draw)
        # Conectar a instrumentos
        self.i_src = Keithley220('GPIB0::12::INSTR')
        self.electrometro = Keithley617('GPIB0::28::INSTR')
        self.matriz = Keithley705('GPIB0::29::INSTR')
        self.instruments = [self.i_src, self.matriz, self.electrometro]
        init = LantzInitializeDialog(self.instruments, parent=self)
        init.finished.connect(self.on_init_finished)
        init.show()

    @pyqtSlot(bool)
    def on_init_finished(self, success):
        self.simulate = not success
        if not self.simulate:
            self.matriz.reset()
        logger.debug("Initialization finished: %s", str(success))
        self.setMidiendo(False)
        self.savesettings = SaveSettings([
            ('corriente_inicial', 'text'),
            ('corriente_final', 'text'),
            ('incremento', 'text'),
            ('puntos_por_decada', 'text'),
            ('lineal', 'checked'),
            ('geometrico', 'checked'),
            ('invertir_polaridad', 'checked'),
            ('invertir_orden', 'checked'),
            ('xlog', 'checked'),
            ('ylog', 'checked'),
            ], self)

    def closeEvent(self, event):
        self.savesettings.save()
        # TODO: interrupt measurement
        if self.midiendo:
            event.ignore()
            return
        init = LantzInitializeDialog(self.instruments, finalize=True)
        init.show()
        return super().closeEvent(event)

    @pyqtSlot(bool)
    def on_lineal_toggled(self, state):
        self.ui.incremento.setEnabled(state)

    @pyqtSlot(bool)
    def on_geometrico_toggled(self, state):
        self.ui.puntos_por_decada.setEnabled(state)

    @asyncio.coroutine
    def medir(self):
        self.setMidiendo(True)
        yield from self.matriz.matrix_mode_async()
        yield from self.matriz.close_async((2, 1))
        yield from self.matriz.close_async((4, 2))
        yield from self.matriz.close_async((4, 3))
        yield from self.matriz.close_async((4, 4))
        yield from self.electrometro.update_async(zero_check = False,
                zero_correct = False)
        yield from self.i_src.update_async(
            current=self.corrientes[0],
            voltage_limit = Q_(15, 'V'),
            output = True)
        # Stabilize output
        yield from asyncio.sleep(.5)
        for ii, corriente in enumerate(self.corrientes):
            if self.ui.invertir_polaridad.isChecked():
                yield from self.i_src.update_async(current=-corriente)
            else:
                yield from self.i_src.update_async(current=corriente)
            logger.debug('Corriente %03d/%03d: %s', ii + 1,
                    len(self.corrientes), '{:.3e~}'.format(corriente))
            tension, nn = yield from self.electrometro.stable_voltage_async(
                    .01)
            logger.debug('Tensión: %s (%d mediciones)',
                    '{:.3e~}'.format(tension), nn)
            self.tensiones[ii] = tension
            self.lines.set_xdata(self.corrientes[:ii+1].magnitude)
            self.lines.set_ydata(self.tensiones[:ii+1].magnitude)
            self.plot.canvas.draw()

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

    @asyncio.coroutine
    def simular(self):
        self.tensiones = (self.corrientes * Q_(1,'kohm')).to('V')
        for ii, corriente in enumerate(self.corrientes):
            yield from asyncio.sleep(.2)
            logger.debug('Corriente %03d/%03d: %s', ii + 1,
                    len(self.corrientes), '{:.3e~}'.format(corriente))
            yield from asyncio.sleep(.2)
            tension = (corriente * Q_(1, 'kohm')).to('V')
            logger.debug('Tensión: %s (%d mediciones)',
                    '{:.3e~}'.format(tension), 0)
            self.tensiones[ii] = tension
            self.lines.set_xdata(self.corrientes[:ii].magnitude)
            self.lines.set_ydata(self.tensiones[:ii].magnitude)
            self.plot.canvas.draw()

    @pyqtSlot()
    @taskwrap.taskwrap
    def on_empezar_clicked(self):
        logger.debug('Empezar')
        corriente_inicial = Q_(self.ui.corriente_inicial.text()).to('A')
        corriente_final = Q_(self.ui.corriente_final.text()).to('A')
        if self.ui.lineal.isChecked():
            incremento = Q_(self.ui.incremento.text()).to('A')
            self.corrientes = arange(corriente_inicial, corriente_final,
                    incremento)
        else:
            puntos_por_decada = int(self.ui.puntos_por_decada.text())
            self.corrientes = logspace(corriente_inicial, corriente_final,
                    puntos_por_decada)
        if self.ui.invertir_orden.isChecked():
            self.corrientes = self.corrientes[::-1]
        logger.debug('Voy a medir corrientes %s', self.corrientes)
        self.tensiones = Q_(np.empty(len(self.corrientes)), 'V')
        self.lines, = self.plot.axes.plot([], [], 'x', label='Hola')
        if not self.simulate:
            try:
                yield from self.medir()
                self.canales = yield from self.matriz.refresh_async('channel')
            except Exception as e:
                logger.error(''.join(traceback.format_exception(*sys.exc_info())))
            finally:
                yield from self.terminar()
        else:
            yield from self.simular()
        filename = get_save_filename(self, caption='Guardar medición',
                filter='*.txt;;*.*')
        if filename == '':
            return
        fd = open(filename, 'w', encoding='utf8')
        fd.write('# Corriente inicial: {:e~}\n'.format(corriente_inicial))
        fd.write('# Corriente final: {:e~}\n'.format(corriente_final))
        if self.ui.lineal.isChecked():
            fd.write('# Incremento: {:e}A\n'.format(incremento))
        else:
            fd.write('# {} puntos por decada\n'.format(puntos_por_decada))
        if self.simulate:
            fd.write('# Simulado con resistencia de 1kOhm\n')
        else:
            tmp = yield from self.electrometro.refresh_async('status')
            fd.write('# Electrómetro: ' + tmp + '\n')
            tmp = yield from self.i_src.refresh_async('status')
            fd.write('# Fuente de corriente: ' + tmp + '\n')
            tmp = yield from self.matriz.refresh_async('status')
            fd.write('# Matriz : ' + tmp + '\n')
            fd.write('# Canales : ' + ''.join(str(k) for k,v in self.canales
                if v) + '\n')
        fd.write('# Corriente[A]\tTension[V]\n')
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
