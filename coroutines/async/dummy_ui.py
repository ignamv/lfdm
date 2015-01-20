from dummygen import DummyGen
from PyQt4.QtGui import QDialog, QPushButton, QTextEdit, QVBoxLayout, QApplication
from PyQt4.uic import loadUi
from PyQt4.QtCore import pyqtSlot, pyqtSignal
from quamash import QEventLoop
from functools import partial
import asyncio
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

def tipi(func):
    logging.debug('tipi(%s)', repr(func))
    def call(*args, **kwargs):
        logging.debug('call(%s,%s,%s)', func, args, kwargs)
        loop = asyncio.get_event_loop()
        logging.debug('loop = %s', repr(loop))
        _coroutine = func(*args, **kwargs)
        logging.debug('handle = %s', loop.create_task(_coroutine))
    return call

class UI(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = loadUi('dummy_ui.ui', self)
        self.ui.correr.clicked.connect(self.on_correr_clicked)
        self.inst = DummyGen()
        self.inst.initialize()

    @pyqtSlot()
    @tipi
    @asyncio.coroutine
    def on_correr_clicked(self):
        try:
            logging.debug('on_correr_clicked')
            fut = self.inst.refresh_async('voltage')
            #fut = asyncio.async(asyncio.sleep(3, 42))
            logging.debug('future = %s', fut)
            tension = yield from fut
            logging.debug('future = %s', fut)
            #tension = yield from 
            logging.debug('Tensión es %s', tension)
        except Exception as e:
            logging.debug('In on_correr_clicked: %s', e)

    @pyqtSlot()
    def on_dummy_clicked(self):
        self.ui.log.append('Dummy')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    logging.debug('loop = %s', repr(loop))
    asyncio.set_event_loop(loop) 
    ui = UI()
    ui.show()
    exit(loop.run_forever())
