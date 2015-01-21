from lantz import Q_
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QTableWidgetItem
from PyQt4.uic import loadUiType
import asyncio
import logging

from taskwrap import taskwrap
from slowdriver import SlowDriver

logging.basicConfig(level=logging.DEBUG)

form, base = loadUiType('ui.ui')

class UI(base):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Try increasing the delay and see it has no effect on the UI
        self.inst = SlowDriver(.2)
        self.inst.initialize()
        self.ui = form()
        self.ui.setupUi(self)

    def setButtonsEnabled(self, value):
        """While running a task, disable buttons and enable 'cancel'"""
        for control in [self.ui.readVoltage, self.ui.sweep]:
            control.setEnabled(value)
        self.ui.cancel.setEnabled(not value)

    @pyqtSlot()
    @taskwrap
    def on_readVoltage_clicked(self):
        """Read instrument voltage and display it"""
        try:
            self.setButtonsEnabled(False)
            voltage = yield from self.inst.refresh_async('voltage')
            self.ui.voltage.setText(str(voltage))
        finally:
            self.setButtonsEnabled(True)

    @pyqtSlot()
    @taskwrap
    def on_sweep_clicked(self):
        """Sweep voltage and record current, display in table"""
        try:
            self.setButtonsEnabled(False)
            self.task = asyncio.Task.current_task()
            voltages = Q_(range(6), 'V')
            self.ui.results.clear()
            self.ui.results.setRowCount(len(voltages))
            for ii, voltage in enumerate(voltages):
                yield from self.inst.update_async(dict(voltage=voltage))
                self.ui.results.setItem(ii, 0, QTableWidgetItem(str(voltage)))
                current = yield from self.inst.refresh_async('current')
                self.ui.results.setItem(ii, 1, QTableWidgetItem(str(current)))
        finally:
            # Turn off the voltage source
            yield from self.inst.update_async(dict(voltage=Q_(0, 'V')))
            self.setButtonsEnabled(True)

    @pyqtSlot()
    def on_cancel_clicked(self):
        self.task.cancel()

if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication
    from quamash import QEventLoop
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    logging.debug('loop = %s', repr(loop))
    asyncio.set_event_loop(loop) 
    ui = UI()
    ui.show()
    exit(loop.run_forever())
