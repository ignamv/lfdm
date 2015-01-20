from enum import Enum
from PyQt4.uic import loadUiType
from PyQt4.QtCore import pyqtSlot, QThread, pyqtSignal
from PyQt4.QtGui import QTableWidget, QDialog, QVBoxLayout
from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg, \
        NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np
from lantz import Q_
from logging import DEBUG, INFO

from lantzinitializedialog import LantzInitializeDialog
from keithley220 import Keithley220
from keithley617 import Keithley617
from keithley705 import Keithley705

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
        self.electrometro = Keithley617('GPIB0::28::INSTR')
        self.matriz = Keithley705('GPIB0::29::INSTR')
        instrumentos = [self.i_src, self.electrometro, self.matriz]
        dialogo = LantzInitializeDialog(instrumentos, self)
        dialogo.show()

        self.setMidiendo(False)

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
        pausa = 2

    class Medicion(QThread):
        corrienteCambio = pyqtSignal(float)
        tensionMedida = pyqtSignal(float)

        def __init__(self, parent, corrientes):
            super().__init__(parent)
            self.corrientes = corrientes

        def run(self):
            try:
                self.medir()
            finally:
                self.terminar()
            self.exit()

        def medir(self):
            i_src = self.parent().i_src
            electrometro = self.parent().electrometro
            matriz = self.parent().matriz

            matriz.channel[(2,1)] = True
            matriz.channel[(4,3)] = True
            electrometro.zero_check = False

            i_src.current = Q_(self.corrientes[0], 'A')
            i_src.voltage_limit = Q_(5, 'V')
            self.parent().i_src.output = True
            for corriente in self.corrientes:
                #i_src.current = Q_(corriente, 'A')
                self.corrienteCambio.emit(corriente)
                #self.tensionMedida.emit(electrometro.stable_voltage())
                self.tensionMedida.emit(corriente * 1e3)

        def terminar(self):
            i_src = self.parent().i_src
            electrometro = self.parent().electrometro
            matriz = self.parent().matriz

            i_src.current = Q_(0, 'A')
            i_src.output = False
            electrometro.zero_check = True
            matriz.reset()

    @pyqtSlot(float)
    def on_corrienteCambio(self, corriente):
        self.corriente = corriente
        INFO.log('Corriente nueva: {}A',corriente)

    @pyqtSlot(float)
    def on_tensionMedida(self, tension):
        print('Tensión medida: {}V'.format(tension))
        self.tensiones[self.puntos] = tension
        self.plot.set_xdata(self.corrientes[:self.puntos])
        self.plot.set_ydata(self.tensiones[:self.puntos])
        self.puntos += 1
        self.canvas.draw()

    def setMidiendo(self, midiendo):
        self.midiendo = midiendo
        self.ui.parametros.setEnabled(not midiendo)
        self.ui.terminar.setEnabled(midiendo)

    @pyqtSlot()
    def on_thread_finished(self):
        self.setMidiendo(False)

    @pyqtSlot()
    def on_empezar_clicked(self):
        corriente_inicial = Q_(self.ui.corriente_inicial.text())\
                .to('A').magnitude
        corriente_final = Q_(self.ui.corriente_final.text())\
                .to('A').magnitude
        if self.ui.lineal.isChecked():
            incremento = Q_(self.ui.incremento.text()).to('A').magnitude
            self.corrientes = np.arange(corriente_inicial, corriente_final,
                    incremento)
        else:
            puntos_por_decada = int(self.parent().ui.puntos_por_decada.text())
            self.corrientes = np.power(10, np.arange(
                np.log10(corriente_inicial), np.log10(corriente_final),
                1. / puntos_por_decada))
        self.tensiones = np.empty(len(self.corrientes))
        self.puntos = 0
        self.plot, = self.axes.plot([], [], 'x', label='Hola')

        self.setMidiendo(True)
        self.thread = self.Medicion(self.corrientes, self)
        self.thread.corrienteCambio.connect(self.on_corrienteCambio)
        self.thread.tensionMedida.connect(self.on_tensionMedida)
        self.thread.start()
        self.thread.finished.connect(self.on_thread_finished)

from PyQt4.QtGui import QApplication
from os import sys

app = QApplication(sys.argv)
ui = VI_GUI()
ui.show()
exit(app.exec_())
