from enum import Enum
from PyQt4.uic import loadUiType
from PyQt4.QtCore import pyqtSlot, QThread
from PyQt4.QtGui import QTableWidget, QDialog, QVBoxLayout
from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg, \
        NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np
from lantz import Q_

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

        self.estado = self.Estado.idle

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
    texto_empezar = { Estado.idle: 'Empezar', Estado.correr: 'Pausa',
            Estado.pausa: 'Continuar'}

    class IniciarMedicion(QThread):
        def run(self):
            self.parent().matriz.channel[(2,1)] = True
            self.parent().matriz.channel[(4,3)] = True

            self.parent().i_src.current = Q_(2, 'nA')
            self.parent().i_src.voltage_limit = Q_(5, 'V')
            #self.parent().i_src.output = True

    @pyqtSlot()
    def on_empezar_clicked(self):
        self.ui.terminar.setEnabled(True)
        if self.estado == self.Estado.idle:
            # Empezar medición
            self.estado = self.Estado.correr
            self.thread = self.IniciarMedicion(self)
            self.thread.start()
        elif self.estado == self.Estado.pausa:
            # Continuar medición
            self.estado = self.Estado.correr
        else:
            # Pausar medición
            self.estado = self.Estado.pausa
            self.thread.wait()
            print('List')
        self.ui.empezar.setText(self.texto_empezar[self.estado])

from PyQt4.QtGui import QApplication
from os import sys

app = QApplication(sys.argv)
ui = VI_GUI()
ui.show()
exit(app.exec_())
