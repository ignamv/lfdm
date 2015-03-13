import logging
import asyncio
import taskwrap

from PyQt4.QtCore import pyqtSlot, QTimer
from PyQt4.uic import loadUiType
from qtdebug import set_trace

from lantzinitializedialog import LantzInitializeDialog
from savesettings import SaveSettings

from lantz import Q_
from keithley705 import Keithley705
from hp4277a import HP4277A

logger = logging.getLogger(__name__)

form, base = loadUiType('contacto.ui')

class Contacto(base):
    npromedios = 5
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = form()
        self.ui.setupUi(self)

        self.matriz = Keithley705('GPIB0::29::INSTR')
        self.hp = HP4277A('GPIB0::17::INSTR')
        self.lcr = self.hp
        self.instruments = [self.matriz, self.hp]
        init = LantzInitializeDialog(self.instruments, parent=self)
        init.finished.connect(self.on_init_finished)
        init.show()

    @pyqtSlot(bool)
    def on_init_finished(self, success):
        if not success:
            self.setEnabled(False)
            return
        self.matriz.reset()
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.probe)
        self.savesettings = SaveSettings([
            ('cmin', 'text'),
            ], self)

    @pyqtSlot()
    def probe(self):
        c, r = self.lcr.measure
        if c > Q_(self.ui.cmin.text()).to('F').magnitude:
            print('\a', end='', flush=True)

    @pyqtSlot(bool)
    def on_activar_toggled(self, state):
        if state:
            self.timer.start()
            for canal in [(3, 2), (3, 3), (3, 4), (5, 1)]:
                self.matriz.close(canal)
        else:
            self.timer.stop()
            self.matriz.reset()

    def closeEvent(self, event):
        self.savesettings.save()
        init = LantzInitializeDialog(self.instruments, finalize=True)
        init.show()
        return super().closeEvent(event)

if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QCoreApplication
    QCoreApplication.setOrganizationName('LFDM')
    QCoreApplication.setApplicationName('Contacto')
    from quamash import QEventLoop
    consola = logging.StreamHandler()
    consola.setLevel(logging.DEBUG)
    logger.addHandler(consola)
    logging.basicConfig(level=logging.DEBUG, filename='error.log', mode='w')
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop) 
    ui = Contacto()
    ui.show()
    exit(loop.run_forever())
    input()

