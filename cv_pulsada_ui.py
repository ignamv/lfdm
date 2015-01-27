from hp8112a import HP8112A
from gwinstekgds2062 import GwinstekGDS2062
from PyQt4.uic import loadUiType
from PyQt4.QtCore import pyqtSlot
from lantzinitializedialog import LantzInitializeDialog
from taskwrap import taskwrap
from cv_pulsada import CV_Pulsada
from lantz import Q_

form, base = loadUiType('cv_pulsada.ui')

class CV_Pulsada_UI(base):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = form()
        self.ui.setupUi(self)
        self.gen = HP8112A('GPIB0::11::INSTR')
        self.osc = GwinstekGDS2062('ASRL5::INSTR')
        init = LantzInitializeDialog([self.gen, self.osc], parent=self)
        init.show()
        self.cv = CV_Pulsada(self.gen, self.osc)

    @pyqtSlot()
    @taskwrap
    def on_pulso_clicked(self):
        self.cv.setAncho(Q_(self.ui.ancho.text()).to('s'))
        yield from self.cv.pulso()
        

if __name__ == '__main__':
    import sys
    import logging
    import asyncio
    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QCoreApplication
    QCoreApplication.setOrganizationName('LFDM')
    QCoreApplication.setApplicationName('CV_Pulsada_GUI')
    from quamash import QEventLoop
    logging.basicConfig(level=logging.DEBUG, filename='error.log', mode='w')
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop) 
    ui = CV_Pulsada_UI()
    ui.show()
    exit(loop.run_forever())
