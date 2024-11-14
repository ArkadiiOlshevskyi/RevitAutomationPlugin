import os
import sys
import json
import logging
import inspect

sys.path.append('C:\Program Files\IronPython 3.4\Lib\site-packages')
logger = logging.getLogger(__name__)


class Dimension:
    """
    Dimension in FML is measurement (used for annotation in plans).
    1) We are parsing data about Dimensions from FML json file.
    2) Then we are creating NewDimension in revit.
    3) Dimension created by using preloaded in ifc template text family.
    ------
    example:
     "dimensions":[
                  {
                     "type":"custom_dimension",
                     "a":{
                        "x":417.7533437422581,
                        "y":657.3025519474583
                     },
                     "b":{
                        "x":417.75334374222274,
                        "y":-567.2974480525414
                     }
                  },

    """

    def __init__(self,
                 ax,
                 ay,
                 bx,
                 by,
                 dimension_type):
        self.ax = ax
        self.ay = ay
        self.bx = bx
        self.by = by
        self.dimension_type = dimension_type

    @classmethod
    def process_config(cls, dimension_config):
        """Process config dimension data"""
        function_name = inspect.currentframe().f_code.co_name
        logger.info('Trying to process config dimension data in {}'.format(function_name))

        try:
            ax = dimension_config.get('a', {}).get('x', 0)
            ay = dimension_config.get('a', {}).get('y', 0)
            bx = dimension_config.get('b', {}).get('x', 0)
            by = dimension_config.get('b', {}).get('y', 0)
            dimension_type = dimension_config.get('type', '')
            return cls(ax, ay, bx, by, dimension_type)
        except Exception as e:
            logger.error('Error: {}, \n Function: {}'.format(e, function_name))
            return None

    def print_parsed_data(self):
        """Just a test print function"""
        print('ax: {}'.format(self.ax))
        print('ay: {}'.format(self.ay))
        print('bx: {}'.format(self.bx))
        print('by: {}'.format(self.by))
        print('dimension_type: {}'.format(self.dimension_type))


def dimension_list_from_fml(input_path, project_name):
    """
    Extracts dimensions from an FML file for a given project.

    input_path -> FML file of the project that contains all needed data.
                   FML can be with extensions like '.fml' or '.json.fml'.
    This list later used to create new models in Revit
    by accessing items attributes.
    """

    function_name = inspect.currentframe().f_code.co_name
    logger.info('Extracting Dimensions to List from FML -> {}'.format(function_name))
    dimension_list = []
    try:
        for file_name in os.listdir(input_path):
            if file_name.endswith('.fml') and file_name.startswith(project_name):
                fml_to_open_path = os.path.join(input_path, file_name)
        with open(fml_to_open_path, 'r') as fml_file:
            fml_data = json.load(fml_file)
        for categories in fml_data['floors']:
            for designs in categories['designs']:
                for labels in designs['dimensions']:
                    new_dimension = Dimension.process_config(labels)
                    dimension_list.append(new_dimension)
        return dimension_list

    except Exception as e:
        logger.error('Error: {}'.format(e))
        return None
