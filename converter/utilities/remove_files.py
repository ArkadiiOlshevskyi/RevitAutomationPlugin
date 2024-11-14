import os
import logging
import inspect

logger = logging.getLogger(__name__)


def remove_files(path, name, extensions):
    """
    Delete files in the specified directory with the specified extensions.
    Use Constant REMOVE_EXTENSIONS
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Deleting files from settled directory -> %s' % function_name)

    if type(name) is not list:
        name = [name]
    for file_name in os.listdir(path):
        for n in name:
            for ext in extensions:
                if file_name.startswith(n) and file_name.endswith(ext):
                    file_path = os.path.join(path, file_name)
                    try:
                        os.remove(file_path)
                        logging.info('Deleted file: %s' % file_path)
                    except Exception as e:
                        logging.error('Error deleting file %s: %s' % (file_path, e))
