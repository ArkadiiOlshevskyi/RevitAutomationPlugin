import logging

logger = logging.getLogger(__name__)


def log_exceptions(cls):
    """
    Decorator used to wrap functions in:
    - try / except form
    - logging (info, error)
    - inspecting(to see failed function project_name in logs).
    """

    def wrapper(*args, **kwargs):
        function_name = cls.__name__
        mod = __import__(cls.__module__)
        mod.root = cls
        try:
            logging.info('Trying => {}'.format(function_name))
            return cls(*args, **kwargs)
        except Exception as e:
            logger.error('Error: {}, \n in Function: {}'.format(e, function_name))
            return None

    return wrapper
