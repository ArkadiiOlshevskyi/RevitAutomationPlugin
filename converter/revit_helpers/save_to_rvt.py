import logging
import inspect
from Autodesk.Revit.DB import *

logger = logging.getLogger(__name__)


def save_project_to_rtv(document, output_path, project_name):
    """
    Save project to RVT file
    :param document:
    :param output_path:
    :param project_name:
    :return:
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Trying to save project to RVT file {}'.format(function_name))
    try:
        save_options = SaveAsOptions()
        save_options.OverwriteExistingFile = True  # Works
        rvt_path = output_path + '\\' + project_name + '.rvt'
        document.SaveAs(rvt_path, save_options)
        logging.info('Revit project saved to RVT file {}'.format(function_name))
    except Exception as e:
        logging.error('Error while saving project to RVT file: {},\n in Function: {}'.format(e, function_name))
        return None
