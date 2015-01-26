from hp8112a import HP8112A
from gwinstekgds2062 import GwinstekGDS2062
from PyQt4.uic import loadUiType

form, base = loadUiType('cv_pulsada.ui')

def CV_Pulsada_UI(base):
    def __init__(self, parent=None):
        super().__init__(self, parent)
        self.ui = form()
        self.ui.setupUi(self)

if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QCoreApplication
    QCoreApplication.setOrganizationName('LFDM')
    QCoreApplication.setApplicationName('CV_Pulsada_GUI')
    from quamash import QEventLoop
    logging.basicConfig(level=logging.DEBUG, filename='error.log', mode='w')
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop) 
    ui = CV_Pulsada_GUI()
    ui.show()
    exit(loop.run_forever())
