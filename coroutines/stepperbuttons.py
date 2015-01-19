from PyQt4.QtGui import QWidget, QHBoxLayout, QPushButton
from PyQt4.QtCore import pyqtSlot
from stepper import Stepper

class StepperButtons(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.run = QPushButton("Run", enabled=False)
        self.pause = QPushButton("Pause")
        self.step = QPushButton("Step")
        self.cancel = QPushButton("Cancel")
        self.layout().addWidget(self.run)
        self.layout().addWidget(self.pause)
        self.layout().addWidget(self.step)
        self.layout().addWidget(self.cancel)

    def connectStepper(self, stepper):
        stepper.statusChanged.connect(self.on_stepper_statusChanged)
        self.run.clicked.connect(stepper.run)
        self.cancel.clicked.connect(stepper.cancel)
        self.pause.clicked.connect(stepper.pause)
        self.step.clicked.connect(stepper.step)
        self.on_stepper_statusChanged(stepper.status)

    def disconnectStepper(self):
        self.run.clicked.disconnect()
        self.cancel.clicked.disconnect()
        self.pause.clicked.disconnect()
        self.step.clicked.disconnect()

    @pyqtSlot(int)
    def on_stepper_statusChanged(self, status):
        self.pause.setEnabled(status == Stepper.RUNNING)
        self.run.setEnabled(status == Stepper.PAUSED)
        self.step.setEnabled(status == Stepper.PAUSED)
        self.cancel.setEnabled(status != Stepper.FINISHED)

