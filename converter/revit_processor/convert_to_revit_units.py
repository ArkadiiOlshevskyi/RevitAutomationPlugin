import sys
import math  # for radians in revit rotation parameter
import logging

sys.path.append(r'~\converter\utils')

logger = logging.getLogger(__name__)
DIVIDER_REVIT_MM = 30.48  # THIS IS FIXED VALUE USED TO CONVERT FML CENTIMETERS TO REVIT FOOTS
DIVIDER_TEXT_AREAS_SURFACES = 25.7  # THIS IS FIXED VALUE USED TO CONVERT FML CENTIMETERS TO REVIT FOOTS
SqFeets_to_SqMeters = 0.09290304
"""IF WE CHANGE NUMBERS FOR UNIT CONVERT WE DO IT ONLY HERE!!!!"""
# TODO - text(areaLabels) coordinates values:
x_text = 1
y_text = 1

def log_exceptions(func):
    """
    Decorator used to wrap functions in:
    - try / except form
    - logging (info, error)
    - inspecting(to see failed function project_name in logs).
    """

    def wrapper(*args, **kwargs):
        function_name = func.__name__
        try:
            logging.info('Trying to parse FML file {}'.format(function_name))
            return func(*args, **kwargs)
        except Exception as e:
            logger.error('Error: {}, \n in Function: {}'.format(e, function_name))
            print('Error: {}, \n in Function: {}'.format(e, function_name))
            return None

    return wrapper


@log_exceptions
def x_revit(x_fml):
    if x_fml == 0:
        return 0
    else:
        x = x_fml / float(DIVIDER_REVIT_MM)
        return x


@log_exceptions
def x_text_revit(x_fml):
    """
    Only for converting the text from Areas nad Surfaces annotation
    @param x_fml:
    @return:
    """
    if x_fml == 0:
        return 0
    else:
        x = x_fml / float(DIVIDER_TEXT_AREAS_SURFACES)
        return x


@log_exceptions
def y_revit(y_fml):
    if y_fml == 0:
        return 0
    else:
        y = y_fml / float(DIVIDER_REVIT_MM) * -1  # * -1 because of Revit Y axis is opposite to FML Y axis
        return y


@log_exceptions
def y_text_revit(y_fml):
    """
    Only for converting the text from Areas nad Surfaces annotation

    @param y_fml:
    @return:
    """
    # TODO - WORK with None
    if y_fml == 0:
        return 0
    else:
        y = y_fml / float(DIVIDER_TEXT_AREAS_SURFACES) * -1  # * -1 because of Revit Y axis is opposite to FML Y axis
        return y


@log_exceptions
def z_revit(z_fml):
    if z_fml == 0:
        return 0
    else:
        z = z_fml / DIVIDER_REVIT_MM
    return z


@log_exceptions
def width_revit(width_fml):
    width = width_fml / DIVIDER_REVIT_MM
    return width


@log_exceptions
def height_revit(height_fml):
    height = height_fml / DIVIDER_REVIT_MM
    return height


@log_exceptions
def z_height_revit(z_height_fml):
    if z_height_fml == 0:
        return 0
    else:
        z_height = z_height_fml / DIVIDER_REVIT_MM
    return z_height


@log_exceptions  # Version works 100% success
def rotation_revit(rotation_fml):
    """
    In Floor planer, in FML file are different values for rotation and flipped Y axis, that's why formula is so strange
    """
    print('Original rotation value from fml -> {}'.format(rotation_fml))
    adjusted_rotation_fml = ((rotation_fml - 270) % 360) * (
        -1)  # Adjust rotation by adding 90 degrees and ensure result is within [0, 360) range
    rotation_rad = math.radians(adjusted_rotation_fml)
    return rotation_rad


@log_exceptions  # Version works 100% success
def rotation_label_revit(rotation_fml):
    """
    In Floor planer, in FML file are different values for rotation and flipped Y axis, that's why formula is so strange
    """
    print('Original rotation value from fml -> {}'.format(rotation_fml))
    rotation_rad = -math.radians(rotation_fml)
    return rotation_rad



# test on custom fill text
x = 42
y = 6
processed_x = x_revit(x)
print('X -> {}'.format(processed_x))
processed_y = y_revit(y)
print('y -> {}'.format(processed_y))

