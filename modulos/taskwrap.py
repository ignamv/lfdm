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
    logger.error('Task DIED: %s', str(handle))
    stream = io.StringIO()
    handle.print_stack(file=stream)
    logger.error(stream.getvalue())
    logger.error('%s: %s', str(type(exception)), str(exception))

def taskwrap(fn):
    """Wrap coroutine. Resulting function starts coroutine in event loop."""
    coroutine = asyncio.coroutine(fn)

    @functools.wraps(fn)
    def create_task(*args, **kwargs):
        logger.debug('Create task %s', fn.__name__)
        loop = asyncio.get_event_loop()
        task = asyncio.async(coroutine(*args, **kwargs))
        task.add_done_callback(task_died)
    return create_task
