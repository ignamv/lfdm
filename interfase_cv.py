
from PyQt4 import uic
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import pyqtSlot
from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

class Interfase(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi('medicion_cv.ui', self)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ui.layout_graficos.addWidget(self.canvas)

    @pyqtSlot()
    def on_boton_clicked(self):
        ax = self.figure.add_subplot(1,1,1)
        xx = np.linspace(0, 2*np.pi, 100)
        ax.plot(xx, np.sin(xx))
        self.canvas.draw()

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    from os import sys
    app = QApplication(sys.argv)
    ventana = Interfase()
    ventana.show()
    exit(app.exec_())
