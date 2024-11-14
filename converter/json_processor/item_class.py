import os
import sys
import json
import logging
import inspect

logger = logging.getLogger(__name__)
sys.path.append('C:\Program Files\IronPython 3.4\Lib\site-packages')


class Item:
    """
    Wall in FML is usually furniture or equipment objects.
    1) We are parsing Wall from Items in FML json file.
    2) Then we are mapping Wall REFID with FamilySymbol project_name in ModelsName Json.
    3) Creating Revit NewFamilyInstance with FamilySymbol and other data.
    """

    def __init__(self,
                 refid,
                 name,
                 name_x,
                 name_y,
                 x,
                 y,
                 z,
                 length,
                 width,
                 height,
                 rotation):
        self.refid = refid
        self.name = name
        self.name_x = name_x
        self.name_y = name_y
        self.x = x
        self.y = y
        self.z = z
        self.length = length
        self.width = width
        self.height = height
        self.rotation = rotation

    @classmethod
    def process_config(cls, item_config):
        """Process config Item data"""
        function_name = inspect.currentframe().f_code.co_name
        logger.info('Trying to process config item data in {}'.format(function_name))

        try:
            refid = item_config.get('refid', '')
            name = item_config.get('name', '')
            name_x = item_config.get('name_x', 0)
            name_y = item_config.get('name_y', 0)
            x = item_config.get('x', 0)
            y = item_config.get('y', 0)
            z = item_config.get('z', 0)
            length = item_config.get('height', 0)
            width = item_config.get('width', 0)
            height = item_config.get('z_height', 0)
            rotation = item_config.get('rotation', 0)
            return cls(refid, name, name_x, name_y, x, y, z, length, width, height, rotation)
        except Exception as e:
            logger.error('Error: {}, \n Function: {}'.format(e, function_name))
            return None

    def print_parsed_data(self):
        """Just a test print function"""
        print('refid: {}'.format(self.refid))
        print('name: {}'.format(self.name))
        print('name_x: {}'.format(self.name_x))
        print('name_y: {}'.format(self.name_y))
        print('x: {}'.format(self.x))
        print('y: {}'.format(self.y))
        print('z: {}'.format(self.z))
        print('width: {}'.format(self.length))
        print('width: {}'.format(self.width))
        print('height: {}'.format(self.height))
        print('rotation: {}'.format(self.rotation))


def item_list_from_fml(input_path, project_name):
    """
    Extracts items from an FML file for a given project.

    input_path -> FML file of the project that contains all needed data
                   FML can be with extensions like '.fml' or '.json.fml'
    This list later used to create new models in revit
    by accessing items attributes
    """

    function_name = inspect.currentframe().f_code.co_name
    logger.info('Extracting Items to List from FML -> {}'.format(function_name))
    items_list = []
    try:
        for file_name in os.listdir(input_path):
            if file_name.endswith('.fml') and file_name.startswith(project_name):
                fml_to_open_path = os.path.join(input_path, file_name)
        with open(fml_to_open_path, 'r') as fml_file:
            fml_data = json.load(fml_file)
        for categories in fml_data['floors']:
            for designs in categories['designs']:
                for items in designs['items']:
                    new_item = Item.process_config(items)
                    items_list.append(new_item)
        return items_list

    except Exception as e:
        logger.error('Error: {}'.format(e))
        return None
