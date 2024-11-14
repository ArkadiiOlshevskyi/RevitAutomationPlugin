import os
import sys
import json
import logging
import inspect

sys.path.append(r'C:\Program Files\IronPython 3.4\Lib\site-packages')

logger = logging.getLogger(__name__)


class Area:
    def __init__(self,
                 room_style_id,
                 color,
                 rotation,
                 name,
                 custom_name,
                 role,
                 name_x,
                 name_y,
                 show_surface_area,
                 show_area_label,
                 poly):
        self.room_style_id = room_style_id
        self.color = color
        self.rotation = rotation
        self.name = name
        self.customName = custom_name
        self.role = role
        self.name_x = name_x
        self.name_y = name_y
        self.showSurfaceArea = show_surface_area
        self.showAreaLabel = show_area_label
        self.poly = poly

    """
    Area in FML is used for marking zones (rooms) in floor plan.
    Main difference between areas and surfaces is that
    area has "showSurfaceArea" feature
    """

    @classmethod
    def process_config(cls, area_config):
        """Process config Area data"""
        function_name = inspect.currentframe().f_code.co_name
        logger.info('Trying to process config Areas data in {}'.format(function_name))

        try:
            room_style_id = area_config.get('room_style_id', '')
            color = area_config.get('color', 0)
            rotation = area_config.get('rotation', 0)
            name = area_config.get('name', 0)
            custom_name = area_config.get('customName', 0)
            role = area_config.get('role', 0)
            name_x = area_config.get('name_x', 0)
            name_y = area_config.get('name_y', 0)
            show_surface_area = area_config.get('showSurfaceArea', 0)
            show_area_label = area_config.get('showAreaLabel', 0)
            poly = area_config.get('poly', [])
            return cls(room_style_id,
                       color,
                       rotation,
                       name,
                       custom_name,
                       role,
                       name_x,
                       name_y,
                       show_surface_area,
                       show_area_label,
                       poly)
        except Exception as e:
            logger.error('Error: {}, \n Function: {}'.format(e, function_name))
            return None

    def print_parsed_data(self):
        """Just a test print function"""
        print('Area. Room Style ID: {}'.format(self.room_style_id))
        print('Area. Color: {}'.format(self.color))
        print('Area. Rotation: {}'.format(self.rotation))
        print('Area. Name: {}'.format(self.name))
        print('Area. Custom Name: {}'.format(self.customName))
        print('Area. Role: {}'.format(self.role))
        print('Area. Name X: {}'.format(self.name_x))
        print('Area. Name Y: {}'.format(self.name_y))
        print('Area. Show Surface Area: {}'.format(self.showSurfaceArea))
        print('Area. Show Area Label: {}'.format(self.showAreaLabel))
        print('Area. Polygon Points: {}'.format(self.poly))


def area_objects_list_from_fml(input_path, project_name):
    """
    Extracts Areas from an FML file for a given project.

    input_path -> FML file of the project that contains all needed data
                   FML can be with extensions like '.fml' or '.json.fml'
    This list later used to create new models in revit
    by accessing items attributes
    """

    function_name = inspect.currentframe().f_code.co_name
    logger.info('Extracting Areas to List from FML -> {}'.format(function_name))
    areas_objects_items_list = []

    try:
        for file_name in os.listdir(input_path):
            if file_name.endswith('.fml') and file_name.startswith(project_name):
                fml_to_open_path = os.path.join(input_path, file_name)
        with open(fml_to_open_path, 'r') as fml_file:
            fml_data = json.load(fml_file)
        for categories in fml_data['floors']:
            for designs in categories['designs']:
                for areas in designs['areas']:
                    new_item = Area.process_config(areas)
                    areas_objects_items_list.append(new_item)
        return areas_objects_items_list

    except Exception as e:
        logger.error('Error: {}'.format(e))
        return None
