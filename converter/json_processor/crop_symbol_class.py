import os
import sys
import json
import logging
import inspect

sys.path.append('C:\Program Files\IronPython 3.4\Lib\site-packages')
logger = logging.getLogger(__name__)


class CropPoint:
    """
    CropPoint in FML used to set Min and Max points in bounding box for cropping view.
    """

    def __init__(self,
                 refid,
                 x,
                 y,
                 z,
                 name,
                 showLabel,
                 name_x,
                 name_y,
                 width,
                 length,
                 height,
                 rotation):
        self.refid = refid
        self.x = x
        self.y = y
        self.z = z
        self.name = name
        self.showLabel = showLabel
        self.name_x = name_x
        self.name_y = name_y
        self.width = width
        self.length = length
        self.height = height
        self.rotation = rotation

    @classmethod
    def process_config(cls, croppoint_config):
        """Process config CropPoint data"""
        function_name = inspect.currentframe().f_code.co_name
        logger.info('Trying to process config item data in {}'.format(function_name))

        try:
            refid = croppoint_config.get('refid', '')
            x = croppoint_config.get('x', 0)
            y = croppoint_config.get('y', 0)
            z = croppoint_config.get('z', 0)
            name = croppoint_config.get('name', 0)
            showLabel = croppoint_config.get('showLabel', 0)
            name_x = croppoint_config.get('name_x', 0)
            name_y = croppoint_config.get('name_y', 0)
            width = croppoint_config.get('width', 0)
            length = croppoint_config.get('height', 0)
            height = croppoint_config.get('z_height', 0)
            rotation = croppoint_config.get('rotation', 0)
            return cls(refid,
                       x,
                       y,
                       z,
                       name,
                       showLabel,
                       name_x,
                       name_y,
                       width,
                       length,
                       height,
                       rotation)
        except Exception as e:
            logger.error('Error: {}, \n Function: {}'.format(e, function_name))
            return None

    def print_parsed_data(self):
        """Just a test print function"""
        print('refid: {}'.format(self.refid))
        print('x: {}'.format(self.x))
        print('y: {}'.format(self.y))
        print('z: {}'.format(self.z))
        print('name: {}'.format(self.name))
        print('showLabel: {}'.format(self.showLabel))
        print('name_x: {}'.format(self.name_x))
        print('name_y: {}'.format(self.name_y))
        print('width: {}'.format(self.width))
        print('length: {}'.format(self.length))
        print('height: {}'.format(self.height))
        print('rotation: {}'.format(self.rotation))


def crop_point_list_from_fml(input_path, project_name):
    """
    Extracts CropPoints from an FML file for a given project.

    input_path -> FML file of the project that contains all needed data
                   FML can be with extensions like '.fml' or '.json.fml'
    This list later used to create new models in revit
    by accessing items attributes
    """

    function_name = inspect.currentframe().f_code.co_name
    logger.info('Extracting CropPoints to List from FML -> {}'.format(function_name))
    items_list = []
    try:
        for file_name in os.listdir(input_path):
            if file_name.endswith('.fml') and file_name.startswith(project_name):
                fml_to_open_path = os.path.join(input_path, file_name)
        with open(fml_to_open_path, 'r') as fml_file:
            fml_data = json.load(fml_file)
        for categories in fml_data['floors']:
            for designs in categories['designs']:
                for crop_points in designs['items']:
                    new_croppoint = CropPoint.process_config(crop_points)
                    items_list.append(new_croppoint)

        crop_points = []
        for crop_point_obj in items_list:
            object_refid = crop_point_obj.refid
            if object_refid == "sym-16":
                crop_points.append(crop_point_obj)
        return crop_points

    except Exception as e:
        logger.error('Error: {}'.format(e))
        return None

