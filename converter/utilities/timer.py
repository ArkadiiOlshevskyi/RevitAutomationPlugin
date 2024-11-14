import time
import logging

logger = logging.getLogger(__name__)


def timer(func):
    """
    Function to measure an execution time for a function or script.
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logging.info('Function %s executed in %s seconds.', func.__name__, end_time - start_time)
        return result

    return wrapper
