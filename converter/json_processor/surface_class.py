import os
import sys
import json
import logging
import inspect

sys.path.append(r'C:\Program Files\IronPython 3.4\Lib\site-packages')

logger = logging.getLogger(__name__)


class Surface:
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
    Surface in FML is used for marking other zones or overlying (rooms) in floor plan.
    For example, you have a main living room (two rooms united)
    but you want to show area, or highlight other room to
    """

    @classmethod
    def process_config(cls, surface_config):
        """Process config Surface data"""
        function_name = inspect.currentframe().f_code.co_name
        logger.info('Trying to process config Surface data in {}'.format(function_name))

        try:
            room_style_id = surface_config.get('room_style_id', '')
            color = surface_config.get('color', 0)
            rotation = surface_config.get('rotation', 0)
            name = surface_config.get('name', 0)
            custom_name = surface_config.get('customName', 0)
            role = surface_config.get('role', 0)
            name_x = surface_config.get('name_x', 0)
            name_y = surface_config.get('name_y', 0)
            show_surface_area = surface_config.get('showSurfaceArea', 0)
            show_area_label = surface_config.get('showAreaLabel', 0)
            poly = surface_config.get('poly', [])

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
        print('Surf. Room Style ID: {}'.format(self.room_style_id))
        print('Surf. Color: {}'.format(self.color))
        print('Surf. Rotation: {}'.format(self.rotation))
        print('Surf. Name: {}'.format(self.name))
        print('Surf. Custom Name: {}'.format(self.customName))
        print('Surf. Role: {}'.format(self.role))
        print('Surf. Name X: {}'.format(self.name_x))
        print('Surf. Name Y: {}'.format(self.name_y))
        print('Surf. Show Surface Area: {}'.format(self.showSurfaceArea))
        print('Surf. Show Area Label: {}'.format(self.showAreaLabel))
        print('Surf. Polygon Points: {}'.format(self.poly))


def area_objects_list_from_fml(input_path, project_name):
    """
    Extracts Surfaces from an FML file for a given project.

    input_path -> FML file of the project that contains all needed data
                   FML can be with extensions like '.fml' or '.json.fml'
    This list later used to create new models in revit
    by accessing items attributes
    """

    function_name = inspect.currentframe().f_code.co_name
    logger.info('Extracting Surcafes to List from FML -> {}'.format(function_name))
    surfaces_objects_items_list = []
    try:
        for file_name in os.listdir(input_path):
            if file_name.endswith('.fml') and file_name.startswith(project_name):
                fml_to_open_path = os.path.join(input_path, file_name)
        with open(fml_to_open_path, 'r') as fml_file:
            fml_data = json.load(fml_file)
        for categories in fml_data['floors']:
            for designs in categories['designs']:
                for surfaces in designs['surfaces']:
                    new_item = Surface.process_config(surfaces)
                    surfaces_objects_items_list.append(new_item)
        return surfaces_objects_items_list

    except Exception as e:
        logger.error('Error: {}'.format(e))
        return None
