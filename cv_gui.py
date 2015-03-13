import logging
import asyncio
import taskwrap
import numpy as np

from PyQt4.QtCore import pyqtSlot
from PyQt4.uic import loadUiType
from qtdebug import set_trace

from lantzinitializedialog import LantzInitializeDialog
from savesettings import SaveSettings
from autoincrement_file import get_save_filename
from util import arange, linspace

from lantz import Q_
from keithley705 import Keithley705
from gwinsteklcr8110g import GwinstekLCR8110G
from hp4277a import HP4277A

logger = logging.getLogger(__name__)

form, base = loadUiType('cv.ui')

class CV_GUI(base):
    npromedios = 5
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = form()
        self.ui.setupUi(self)

        self.matriz = Keithley705('GPIB0::29::INSTR')
        self.gwinstek = GwinstekLCR8110G(port=0, timeout=5)
        self.hp = HP4277A('GPIB0::17::INSTR')
        self.lcr = self.gwinstek
        self.instruments = [self.matriz, self.hp, self.gwinstek]
        init = LantzInitializeDialog(self.instruments, parent=self)
        init.finished.connect(self.on_init_finished)
        init.show()

    @pyqtSlot(bool)
    def on_init_finished(self, success):
        if not success:
            self.ui.estado.setText("Inicialización falló")
            self.setEnabled(False)
            return
        self.matriz.reset()
        self.setMidiendo(False)
        self.savesettings = SaveSettings([
            ('frecuencia', 'text'),
            ('gwinstek', 'checked'),
            ('hp', 'checked'),
            ('inicial', 'text'),
            ('ffinal', 'text'),
            ('paso', 'text'),
            ('radiopaso', 'checked'),
            ('puntos', 'text'),
            ('radiopuntos', 'checked'),
            ('volver', 'checked'),
            ('pausa', 'text'),
            ], self)

    @pyqtSlot(bool)
    def on_radiopaso_toggled(self, state):
        self.ui.paso.setEnabled(state)

    @pyqtSlot(bool)
    def on_hp_toggled(self, state):
        if state:
            self.lcr = self.hp

    @pyqtSlot(bool)
    def on_gwinstek_toggled(self, state):
        if state:
            self.lcr = self.gwinstek

    @pyqtSlot(bool)
    def on_radiopuntos_toggled(self, state):
        self.ui.puntos.setEnabled(state)

    def setMidiendo(self, midiendo):
        self.midiendo = midiendo
        self.ui.estado.setText(["Detenido", "Midiendo"][midiendo])
        self.ui.parametros.setEnabled(not midiendo)
        self.ui.lcr.setEnabled(not midiendo)
        self.ui.detener.setEnabled(midiendo)

    def closeEvent(self, event):
        self.savesettings.save()
        # TODO: interrupt measurement
        if self.midiendo:
            event.ignore()
            return
        init = LantzInitializeDialog(self.instruments, finalize=True)
        init.show()
        return super().closeEvent(event)

    @asyncio.coroutine
    def medir(self):
        filename = get_save_filename(self, caption='Guardar medición',
                filter='*.txt;;*.*')
        if filename == '':
            return
        for canal in [(3, 2), (3, 3), (3, 4), (5, 1)]:
            yield from self.matriz.close_async(canal)
        yield from self.lcr.update_async(equivalent_circuit = 'parallel',
                frequency = Q_(self.ui.frecuencia.text()).to('Hz'))

        if self.lcr is self.hp:
            yield from self.hp.update_async(functionA='C', functionB='ESR',
                    drive_level='low')
        else:
            yield from self.lcr.update_async(drive_level = Q_(20, 'mV'))
        if self.ui.radiopaso.isChecked():
            tensiones = arange(Q_(self.ui.inicial.text()).to('V'),
                               Q_(self.ui.ffinal.text()).to('V'),
                               Q_(self.ui.paso.text()).to('V'))
        else:
            tensiones = linspace(Q_(self.ui.inicial.text()).to('V'),
                                 Q_(self.ui.ffinal.text()).to('V'),
                                 int(self.ui.puntos.text()))
        if self.ui.volver.isChecked():
            tensiones = Q_(np.concatenate((tensiones, tensiones[::-1])), 'V')
        yield from self.hp.update_async(bias_voltage = tensiones[0])
        yield from asyncio.sleep(1)
        cv = np.zeros((len(tensiones), 2))
        for ii, tension in enumerate(tensiones):
            self.ui.estado.setText("{}/{}".format(ii+1, len(tensiones)))
            logger.debug("Cambiar bias...")
            yield from self.hp.update_async(bias_voltage = tension)
            logger.debug("Pausa...")
            yield from asyncio.sleep(Q_(self.ui.pausa.text()
                ).to('s').magnitude)
            logger.debug("Medir...")
            if self.lcr is self.gwinstek:
                cv[ii,:] = yield from self.lcr.refresh_async('measure')
                cv[ii,1] = 1. / cv[ii, 1]
            else:
                for jj in range(self.npromedios):
                    temp = yield from self.lcr.refresh_async('measure')
                    cv[ii, :] += temp
                cv[ii, :] /= self.npromedios
        yield from self.hp.update_async(bias_voltage = Q_(0, 'V'))
        vsrc_learn = yield from self.hp.refresh_async('learn')
        freq, circ, drive = yield from self.lcr.refresh_async(['frequency',
            'equivalent_circuit', 'drive_level'])
        matriz_learn = yield from self.matriz.refresh_async('status')
        cabecera = """\
{args}
Bias: {vsrc}
LCR: {circ} {freq} {drive}
Matriz: {matriz}
Tensión [V]\tC [F]\tG [S]""".format(args = " ".join(sys.argv),
            vsrc = vsrc_learn, circ = circ, freq = freq, drive = drive,
            matriz = matriz_learn)
        np.savetxt(filename, np.column_stack((tensiones, cv)), header=cabecera)

    @asyncio.coroutine
    def terminar(self):
        yield from self.matriz.reset_async()
        yield from self.hp.update_async(bias_voltage = Q_(0, 'V'))

    @pyqtSlot()
    def on_detener_clicked(self):
        self.medir_task.cancel()

    @pyqtSlot()
    @taskwrap.taskwrap
    def on_barrer_clicked(self):
        self.medir_task = asyncio.Task.current_task()
        self.setMidiendo(True)
        try:
            yield from self.medir()
        finally:
            yield from self.terminar()
            self.setMidiendo(False)

if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QCoreApplication
    QCoreApplication.setOrganizationName('LFDM')
    QCoreApplication.setApplicationName('CV_GUI')
    from quamash import QEventLoop
    consola = logging.StreamHandler()
    consola.setLevel(logging.DEBUG)
    logger.addHandler(consola)
    #logging.basicConfig(level=logging.DEBUG, filename='error.log', mode='w')
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop) 
    ui = CV_GUI()
    ui.show()
    exit(loop.run_forever())
    input()
