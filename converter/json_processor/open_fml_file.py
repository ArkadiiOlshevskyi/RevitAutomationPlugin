import os
import json
import inspect
import logging

logger = logging.getLogger(__name__)


def load_json(file_path, project_name):
    """
    Input:
    Load JSON data from a file.
    - file_path (str): The path to the JSON file.
    Returns:
    - dict or None: The loaded JSON data, or None if an error occurs.
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Trying to load json file in {}'.format(function_name))

    try:
        for file_name in os.listdir(file_path):
            if file_name.endswith('.fml') and file_name.startswith(project_name):
                fml_to_open_path = os.path.join(file_path, file_name)
        with open(fml_to_open_path, 'r') as fml_file:
            fml_data = json.load(fml_file)
        logger.info('Successfully loaded Json -> : {}'.format(fml_to_open_path))
        return fml_data

    except Exception as e:
        logger.error('Error while loading json: {}. \n Function: {}'.format(e, function_name))
        return None
