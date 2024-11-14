import logging
import inspect
from Autodesk.Revit.DB import XYZ

logging.getLogger(__name__)


def get_orientation_point(point):
    """
    Getting orientation point for Revit model.
    """

    function_name = inspect.currentframe().f_code.co_name
    logging.info('Trying to get orientation point...')

    try:
        get_z = point.Z
        orientation_point = point - XYZ(0, 0, get_z)
        return orientation_point

    except Exception as e:
        logging.error('Error: {}, \n Function: {}'.format(e, function_name))
        return None
