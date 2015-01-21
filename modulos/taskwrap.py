import asyncio
import logging
import functools
from io import StringIO

logger = logging.getLogger(__name__)

def task_died(handle):
    """Log dead task's stack trace"""
    stack = StringIO()
    handle.print_stack(file=stack)
    logger.debug(stack.getvalue())

def taskwrap(fn):
    """Wrap coroutine. Resulting function starts coroutine in event loop."""
    coroutine = asyncio.coroutine(fn)

    @functools.wraps(fn)
    def create_task(*args, **kwargs):
        loop = asyncio.get_event_loop()
        task = asyncio.async(coroutine(*args, **kwargs))
        task.add_done_callback(task_died)
    return create_task
