import asyncio
import logging
import functools
from io import StringIO
import sys
import traceback
import io

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
logger.addHandler(console)

def task_died(handle):
    """Log dead task's stack trace"""
    exception = handle.exception()
    if exception is None:
        logger.debug('Task finished: %s', str(handle))
        return
    asyncio.get_event_loop().stop()
    handle.print_stack()

def taskwrap(fn):
    """Wrap coroutine. Resulting function starts coroutine in event loop."""
    coroutine = asyncio.coroutine(fn)

    @functools.wraps(fn)
    def create_task(*args, **kwargs):
        logger.debug('Create task %s', fn.__name__)
        loop = asyncio.get_event_loop()
        task = asyncio.async(coroutine(*args, **kwargs))
        task.add_done_callback(task_died)
        return task
    return create_task

if __name__ == '__main__':
    import quamash
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    loop = quamash.QEventLoop(app)
    asyncio.set_event_loop(loop) 
    @taskwrap
    def f():
        1/0
    f()
    loop.run_until_complete(asyncio.sleep(4))
