import os
import logging
import inspect

logger = logging.getLogger(__name__)


def get_project_name(path, extensions):
    """
    Get project project_name from the given path with file project_name and FML extension.
    Used in Input directory
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Running function: {}'.format(function_name))

    try:
        file_names = []
        for file_name in os.listdir(path):
            if file_name.endswith(tuple(extensions)):
                file_name = os.path.splitext(file_name)[0]
                file_names.append(file_name)

        if file_names:
            return file_names[0]
        else:
            logger.warning("No files with given extensions found in the path.")
            return None

    except Exception as e:
        logger.error('Error: {}, \n in Function: {}'.format(e, function_name))
        return None


def get_project_name_from_path(path):
    """
    Extract the project name from the given file path, handling multiple extensions.
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Running function: {}'.format(function_name))

    try:
        base_name = os.path.basename(path)
        name = base_name.split('.')[0]
        return name
    except Exception as e:
        logger.error('Error: {}, \n in Function: {}'.format(e, function_name))
        return None
