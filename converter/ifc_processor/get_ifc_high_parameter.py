import logging
import inspect
from Autodesk.Revit.DB import *

logging.getLogger(__name__)


def get_high_parameter(face):
    """
    Getting high parameter from IFC model face
    """

    function_name = inspect.currentframe().f_code.co_name
    logging.info('Trying to get high parameter...')

    try:
        for lines in face.GetEdgesAsCurveLoops():
            list_of_lines = list(lines)
            vertical_line_of_planar_face = list_of_lines[1]
            width_parameter = vertical_line_of_planar_face.Length
            return width_parameter

    except Exception as e:
        logging.error('Error: {}, \n Function: {}'.format(e, function_name))
        return None
