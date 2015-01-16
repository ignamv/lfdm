from lantz import LOGGER
from lantz.log import log_to_screen, DEBUG
from os import sys
from PyQt4.QtGui import QApplication, QWidget
from PyQt4.QtCore import pyqtSlot
from PyQt4.uic import loadUi
import logging
from lantz.ui.widgets import connect_driver

from hp8112a import HP8112A

class HP8112A_UI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = loadUi('hp8112a.ui', self)
        self.driver = HP8112A('GPIB0::11::INSTR')
        self.driver.initialize()
        connect_driver(self.ui, self.driver)

    def __del__(self):
        self.driver.finalize()

log_to_screen(DEBUG)
fh = logging.FileHandler('error.log')
fh.setLevel(logging.DEBUG)
LOGGER.addHandler(fh)

app = QApplication(sys.argv)
window = HP8112A_UI()
window.show()
exit(app.exec_())
