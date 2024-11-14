import logging
import inspect
import re

logger = logging.getLogger(__name__)


def ifc_model_refid_name(model_name, prefix):
    """
    Function takes ifc_model project_name from
    pre-selected_level revit list with IFC models
    For example project_name like "Window_218 1526 1526"
    Means that "Window_218" is revit models project_name for
    loading generic revit model
    Input:
    -> models_name - project_name gotten from IFC model.Name
    -> prefix - hardcode search prefix for all IFC models
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Getting model REFID -> {}'.format(function_name))

    try:
        if model_name.startswith(prefix):
            parts = model_name[len(prefix):].split(' ', 1)
            if len(parts) > 0:
                extracted_name = parts[0]
                return extracted_name
            else:
                logger.error("No space found after prefix in the element project_name.")
                return None
        else:
            logger.error("Prefix not found in the element project_name.")
            return None
    except Exception as e:
        logger.error("An error occurred in function {}: {}".format(inspect.stack()[0][3], e))
        return None


def extract_type_refid(input_string):
    """
    Used for updated IFC version from 12-04-2024
    with died walls, windows and doors
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Trying to get ifc model project_name -> {}'.format(function_name))

    try:
        pattern = r'^([A-Za-z_]+_\d+)'
        match = re.search(pattern, input_string)
        if match:
            selected_name = match.group(1)
            selected_name_lower = selected_name.lower()
            return selected_name_lower
        else:
            return None
    except Exception as e:
        logging.error("An error occurred while extracting project_name part: %s", e)
        return None
