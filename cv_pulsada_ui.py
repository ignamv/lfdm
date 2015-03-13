from hp8112a import HP8112A
from gwinstekgds2062 import GwinstekGDS2062
from PyQt4.uic import loadUiType
from PyQt4.QtCore import pyqtSlot
from lantz import Q_
import logging
import os
import numpy as np
from matplotlib import pyplot as plt

from lantzinitializedialog import LantzInitializeDialog
from savesettings import SaveSettings
from autoincrement_file import get_save_filename
from util import logspace
from taskwrap import taskwrap
from cv_pulsada import CV_Pulsada

logger = logging.getLogger(__name__)

form, base = loadUiType('cv_pulsada.ui')

class CV_Pulsada_UI(base):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = form()
        self.ui.setupUi(self)
        self.gen = HP8112A('GPIB0::11::INSTR')
        self.osc = GwinstekGDS2062('ASRL5::INSTR')
        self.instrumentos = [ self.gen, self.osc ]
        self.savesettings = SaveSettings([
            ('high', 'text'),
            ('low', 'text'),
            ('rise', 'text'),
            ('fall', 'text'),
            ('inicial', 'text'),
            ('tfinal', 'text'),
            ('guardar_primeros', 'text'),
            ('puntos_por_decada', 'text')], self)
        init = LantzInitializeDialog(self.instrumentos, parent=self)
        init.finished.connect(self.on_init_finished)
        init.show()

    @pyqtSlot(bool)
    def on_init_finished(self, success):
        if not success:
            self.close()
        self.cv = CV_Pulsada(self.gen, self.osc)

    def closeEvent(self, event):
        self.savesettings.save()
        super().closeEvent(event)

    @pyqtSlot()
    @taskwrap
    def on_config_gen_clicked(self):
        self.ui.parametros_generador.setEnabled(False)
        yield from self.gen.update_async(
                high_level=Q_(self.ui.high.text()).to('V') / 2,
                low_level=Q_(self.ui.low.text()).to('V') / 2,
                leading_edge=Q_(self.ui.rise.text()).to('s'),
                trailing_edge=Q_(self.ui.rise.text()).to('s'))
        self.ui.parametros_generador.setEnabled(True)

    @pyqtSlot()
    @taskwrap
    def on_barrer_clicked(self):
        dirname = get_save_filename(self, caption='Carpeta para guardar'\
            'medición')
        if dirname == '':
            return
        logger.debug('Guardando en %s', dirname)
        anchos = Q_(logspace(Q_(self.ui.inicial.text()).to('s').magnitude,
                             Q_(self.ui.tfinal.text()).to('s').magnitude,
                             int(self.ui.puntos_por_decada.text())), 's')
        logger.debug('Midiendo %s', str(anchos))
        os.mkdir(dirname)
        yield from self.cv.configurar()
        yield from self.gen.update_async(enable=True)
        guardar_primeros = int(self.ui.guardar_primeros.text())
        for ii, tt in enumerate(anchos):
            logger.debug('%02d / %02d: %s', ii + 1, len(anchos), str(tt))
            yield from self.cv.setAncho(tt, True, ii < guardar_primeros or 
                    tt > self.cv.generador_max)
            yield from self.cv.sleep(Q_(1, 's'))
            pulso = yield from self.cv.pulso()
            comments = """\
CV Pulsada de {} a {}, {} puntos por década
Generador: {}
Osciloscopio: {}
Este es el pulso {}, de ancho {:.2e~}
Tiempo [s]\tCanal 1 [V]\n""".format(
                self.ui.inicial.text(), self.ui.tfinal.text(),
                self.ui.puntos_por_decada.text(), self.gen.settings, 
                self.osc.idn, ii, tt)
            for jj, flanco in enumerate(pulso):
                prefijo = os.path.join(dirname,
                        '{:03d}_{:.2e~}_{:d}'.format(ii, tt, jj))
                tiempo = pulso[jj]['time'].to('s').magnitude
                canal1 = pulso[jj][1].to('V').magnitude
                canal2 = pulso[jj][2].to('V').magnitude
                np.savetxt(prefijo + '.txt', np.column_stack((tiempo, canal1,
                    canal2)), header=comments)
                plt.figure(figsize=(18,9))
                plt.subplot(1,2,1)
                plt.plot(tiempo, canal1)
                plt.xlabel('Tiempo [s]')
                plt.ylabel('Tensión [V]')
                plt.subplot(1,2,2)
                plt.plot(tiempo, canal2)
                plt.xlabel('Tiempo [s]')
                plt.ylabel('Tensión [V]')
                plt.savefig(prefijo + '.png')
                plt.clf()


if __name__ == '__main__':
    import sys
    import asyncio
    from PyQt4.QtGui import QApplication
    from PyQt4.QtCore import QCoreApplication
    QCoreApplication.setOrganizationName('LFDM')
    QCoreApplication.setApplicationName('CV_Pulsada_GUI')
    from quamash import QEventLoop
    logger.setLevel(logging.DEBUG)
    consola = logging.StreamHandler()
    consola.setLevel(logging.DEBUG)
    logger.addHandler(consola)
    archivo = logging.FileHandler('error.log', mode='w')
    logger.addHandler(archivo)
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop) 
    ui = CV_Pulsada_UI()
    ui.show()
    exit(loop.run_forever())
