from PyQt4.uic import loadUiType
from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, Qt
from sys import stdout
from stepper import Stepper
from stepperbuttons import StepperButtons

form, base = loadUiType('form.ui')

class UI(base):
    def __init__(self, parent=None):
        super().__init__()
        self.ui = form()
        self.ui.setupUi(self)
        self.stepperThread = QThread(self)
        self.stepper = VIStepper()
        self.stepper.moveToThread(self.stepperThread)
        self.stepper.finished.connect(self.stepperThread.quit)
        buttons = StepperButtons(self)
        self.layout().addWidget(buttons)
        buttons.connectStepper(self.stepper)
        self.stepperThread.start()

    def closeEvent(self, event):
        self.stepper.cancel()
        self.stepperThread.wait()
        event.accept()

    @pyqtSlot(int)
    def on_stepper_statusChanged(self, status):
        self.ui.pause.setEnabled(status == Stepper.RUNNING)
        self.ui.run.setEnabled(status == Stepper.PAUSED)
        self.ui.step.setEnabled(status == Stepper.PAUSED)
        self.ui.cancel.setEnabled(status != Stepper.FINISHED)
        if status == Stepper.FINISHED:
            self

    @pyqtSlot(str)
    def log(self, message):
        self.ui.log.appendHTML(message)

    @pyqtSlot()
    def on_stepper_finished(self):
        pass

class VIStepper(Stepper):
    initialized = pyqtSignal()
    currentChanged = pyqtSignal()
    voltageMeasured = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.destroyed.connect(self.thread().quit)

    def work(self):
        for ii in range(3):
            print('Current {}...'.format(ii), end='')
            stdout.flush()
            self.thread().msleep(2000)
            print('done')
            self.currentChanged.emit()
            yield
            print('Measure {}...'.format(ii), end='')
            stdout.flush()
            self.thread().msleep(2000)
            print('done')
            self.voltageMeasured.emit()
            yield

    def finalize(self):
        for ii in range(3):
            print('Finalize {}...'.format(ii), end='')
            stdout.flush()
            self.thread().msleep(500)
            print('done')
        self.finished.emit()

from PyQt4.QtGui import QApplication
from os import sys
app = QApplication(sys.argv)
ui = UI()
ui.show()
exit(app.exec_())
