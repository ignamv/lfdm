from PyQt4.QtCore import pyqtSlot, pyqtSignal, QObject, Qt

class Stepper(QObject):
    """Run or step through a task

    Override work(), putting yield statements on breakpoints. The program can
    step through work with the run, pause and step functions or jump to
    finalize() with cancel.

    By calling the slots from another thread you can control concurrent
    execution of work()."""

    stepped = pyqtSignal()
    finished = pyqtSignal()
    statusChanged = pyqtSignal(int)
    (PAUSED, RUNNING, FINISHED) = range(3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._set_status(self.PAUSED)
        self.coroutine = self.create_coroutine()
        # This allows try_step to queue a call to itself after any pause events
        # are handled
        self.stepped.connect(self.try_step, Qt.QueuedConnection)

    def _set_status(self, status):
        self.status = status
        self.statusChanged.emit(status)

    @pyqtSlot()
    def step(self):
        if self.status == self.FINISHED:
            raise Warning('Task finished')
        try:
            next(self.coroutine)
        except StopIteration:
            self._set_status(self.FINISHED)

    @pyqtSlot()
    def run(self):
        self._set_status(self.RUNNING)
        self.try_step()

    @pyqtSlot()
    def cancel(self):
        self.coroutine.close()
        self._set_status(self.FINISHED)

    @pyqtSlot()
    def pause(self):
        self._set_status(self.PAUSED)

    @pyqtSlot()
    def try_step(self):
        if self.status != self.RUNNING:
            return
        self.step()
        self.stepped.emit()

    def create_coroutine(self):
        try:
            yield from self.work()
        finally:
            self.finalize()

    def work(self):
        pass

    def finalize(self):
        pass

