from PyQt4.QtGui import QDialog, QTableWidget, QVBoxLayout
from PyQt4.QtCore import Qt
from lantz.ui.widgets import initialize_and_report

class LantzInitializeDialog(QDialog):
    def __init__(self, instruments, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.setWindowTitle('Initialize instruments')
        self.setWindowModality(Qt.WindowModal)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Class", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.resize(250, 50)
        self.table.resizeColumnToContents(0)
        self.layout().addWidget(self.table)

        self.instruments = instruments

    def showEvent(self, ev):
        super().showEvent(ev)
        self.thread = initialize_and_report(self.table, self.instruments)
        self.thread.finished.connect(self.close)

if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    from keithley220 import Keithley220
    from os import sys

    app = QApplication(sys.argv)
    keith = Keithley220('GPIB0::12::INSTR')
    ui = LantzInitializeDialog([keith])
    ui.show()
    exit(app.exec_())
