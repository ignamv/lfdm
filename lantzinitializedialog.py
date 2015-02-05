import asyncio
from PyQt4.QtGui import QDialog, QTableWidget, QVBoxLayout, QTableWidgetItem, QPushButton
from PyQt4.QtCore import Qt, pyqtSignal, pyqtSlot
import taskwrap
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class LantzInitializeDialog(QDialog):
    # True for success, False if any instruments did not initialize
    finished = pyqtSignal(bool)

    def __init__(self, instruments, parent=None, finalize=False):
        super().__init__(parent)
        self.finalize = finalize
        self.prefix = ['Initial', 'Final'][finalize]
        self.setLayout(QVBoxLayout())
        self.setWindowTitle(self.prefix + 'ize instruments')
        self.setWindowModality(Qt.WindowModal)

        self.table = QTableWidget(len(instruments), 2)
        self.instruments = instruments
        for ii, inst in enumerate(instruments):
            self.table.setItem(ii, 0, QTableWidgetItem(inst.name))
            self.table.setItem(ii, 1, QTableWidgetItem('Pending...'))

        cancel = QPushButton('Cancel')
        cancel.clicked.connect(self.cancel)

        self.table.setHorizontalHeaderLabels(["Name", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.resizeColumnToContents(0)
        self.layout().addWidget(self.table)
        self.layout().addWidget(cancel)
        self.initialize_all()

    @pyqtSlot()
    def cancel(self):
        for fut in self.futures:
            fut.cancel()

    @asyncio.coroutine
    def initialize_instrument(self, instrument):
        logger.debug(self.prefix + 'izing %s', instrument.name)
        row = self.instruments.index(instrument)
        try:
            if self.finalize:
                yield from instrument.finalize_async()
            else:
                yield from instrument.initialize_async()
        except Exception as e:
            logger.error('%sizing %s: %s', self.prefix, instrument.name,
                    str(e))
            self.table.item(row, 1).setText(str(e))
            return False
        self.table.item(row, 1).setText('Done')
        return True

    @taskwrap.taskwrap
    def initialize_all(self):
        self.futures = [asyncio.async(self.initialize_instrument(inst)) 
                    for inst in self.instruments]
        results = yield from asyncio.gather(*self.futures)
        if all(results):
            self.finished.emit(True)
            self.close()
        else:
            self.finished.emit(False)

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    import quamash
    from keithley220 import Keithley220
    from os import sys
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logger.addHandler(console)

    app = QApplication(sys.argv)
    loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(loop) 
    instruments = [
        Keithley220('GPIB0::12::INSTR'),
        #Keithley220('GPIB0::3::INSTR'),
        ]
    ui = LantzInitializeDialog(instruments)
    ui.show()
    exit(loop.run_forever())
