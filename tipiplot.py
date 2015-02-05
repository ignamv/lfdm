from matplotlib.backends import qt_compat
import matplotlib
import matplotlib.figure
import matplotlib.backends.backend_qt4agg
from PyQt4 import QtGui, QtCore

class TipiPlot(QtGui.QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.figure = matplotlib.figure.Figure(frameon=False)
        self.axes = self.figure.add_axes((.1,.1,.85,.85))
        self.axes.hold(True)
        self.canvas = matplotlib.backends.backend_qt4agg.FigureCanvasQTAgg(
                self.figure)
        self.canvas.setMinimumSize(320, 240)
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().addWidget(self.canvas)
        self.layout().addWidget(matplotlib.backends.backend_qt4agg.\
                NavigationToolbar2QT(self.canvas, self))

    scales = ['linear', 'log']
    def logscaleX(self):
        return self.axes.get_xscale() == self.scales[1]

    @QtCore.pyqtSlot(bool)
    def setLogscaleX(self, value):
        self.axes.set_xscale(self.scales[value])

    def logscaleY(self):
        return self.axes.get_yscale() == self.scales[1]

    @QtCore.pyqtSlot(bool)
    def setLogscaleY(self, value):
        print('logy {}'.format(value))
        self.axes.set_yscale(self.scales[value])

    @QtCore.pyqtSlot()
    def draw(self):
        self.canvas.draw()

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = TipiPlot()
    ui.show()
    exit(app.exec_())
