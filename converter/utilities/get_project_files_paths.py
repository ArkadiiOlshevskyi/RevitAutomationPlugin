import os
import logging
import inspect

logger = logging.getLogger(__name__)


def get_file_path(project_name, extension, file_path):
    """
    Get the full file path of a file with a given extension and project project_name within a folder.

    Args:
        project_name (str): The project project_name.
        extension (str): The file extension to search for.
        file_path (str): The path to the folder to search in.

    Returns:
        str: The full file path if found, else an empty string.
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Trying to get file path -> {}'.format(function_name))

    try:
        for file_name in os.listdir(file_path):
            if file_name.endswith(extension) and project_name in file_name:
                return os.path.join(file_path, file_name)

    except Exception as e:
        logging.error('An error occurred: {}'.format(e))
    return ''
