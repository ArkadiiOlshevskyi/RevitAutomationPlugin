import logging
import inspect

logging.getLogger(__name__)


def get_width_parameter(face):
    """
    Getting width parameter from IFC model face
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Trying to get width parameter...')

    try:
        for lines in face.GetEdgesAsCurveLoops():
            list_of_lines = list(lines)
            horizontal_line_of_planar_face = list_of_lines[2]
            width_parameter = horizontal_line_of_planar_face.Length
            return width_parameter

    except Exception as e:
        logging.error('Error: {}, \n Function: {}'.format(e, function_name))
        return None
