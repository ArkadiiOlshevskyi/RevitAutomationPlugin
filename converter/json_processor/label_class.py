import os
import sys
import json
import logging
import inspect

sys.path.append('C:\Program Files\IronPython 3.4\Lib\site-packages')
logger = logging.getLogger(__name__)


class Label:
    """
    Dimension in FML is text (used for annotation in plans).
    1) We are parsing data about Labels from FML json file.
    2) Then we are creating TextNote in revit.
    3) Later rotation can be applied
    4) Dimension created by using preloaded in ifc template text family.
    5) Z coordinate is not used in 3d plan texts
    """

    def __init__(self,
                 x,
                 y,
                 text,
                 fontFamily,
                 fontSize,
                 letterSpacing,
                 fontColor,
                 backgroundColor,
                 align,
                 rotation):
        self.x = x
        self.y = y
        self.text = text
        self.fontFamily = fontFamily
        self.fontSize = fontSize
        self.letterSpacing = letterSpacing
        self.fontColor = fontColor
        self.backgroundColor = backgroundColor
        self.align = align
        self.rotation = rotation

    @classmethod
    def process_config(cls, label_config):
        """Process config label data"""
        function_name = inspect.currentframe().f_code.co_name
        logger.info('Trying to process config label data in {}'.format(function_name))

        try:
            x = label_config.get('x', 0)
            y = label_config.get('y', 0)
            text = label_config.get('text', '')
            fontFamily = label_config.get('fontFamily', 'Arial')
            fontSize = label_config.get('fontSize', 12)
            letterSpacing = label_config.get('letterSpacing', 0)
            fontColor = label_config.get('fontColor', '#000000')
            backgroundColor = label_config.get('backgroundColor', '#FFFFFF')
            align = label_config.get('align', 'left')
            rotation = label_config.get('rotation', 0)

            print('FML Dimension parameters processed....')
            return cls(x, y, text, fontFamily, fontSize,
                       letterSpacing, fontColor,
                       backgroundColor, align, rotation)
        except Exception as e:
            logger.error('Error: {}, \n Function: {}'.format(e, function_name))
            return None

    def print_parsed_data(self):
        """Just a test print function"""
        print('x: {}'.format(self.x))
        print('y: {}'.format(self.y))
        print('text: {}'.format(self.text))
        print('fontFamily: {}'.format(self.fontFamily))
        print('fontSize: {}'.format(self.fontSize))
        print('letterSpacing: {}'.format(self.letterSpacing))
        print('fontColor: {}'.format(self.fontColor))
        print('backgroundColor: {}'.format(self.backgroundColor))
        print('align: {}'.format(self.align))
        print('rotation: {}'.format(self.rotation))


def label_list_from_fml(input_path, project_name):     # Works Tested - not used anymore
    """
    Extracts labels from an FML file for a given project.

    input_path -> FML file of the project that contains all needed data
                   FML can be with extensions like '.fml' or '.json.fml'
    This list later used to create new models in revit
    by accessing items attributes
    """

    function_name = inspect.currentframe().f_code.co_name
    logger.info('Extracting Items to List from FML -> {}'.format(function_name))
    label_list = []
    try:
        for file_name in os.listdir(input_path):
            if file_name.endswith('.fml') and file_name.startswith(project_name):
                fml_to_open_path = os.path.join(input_path, file_name)
        with open(fml_to_open_path, 'r') as fml_file:
            fml_data = json.load(fml_file)
        for categories in fml_data['floors']:
            for designs in categories['designs']:
                for labels in designs['labels']:
                    new_label = Label.process_config(labels)
                    label_list.append(new_label)
        return label_list

    except Exception as e:
        logger.error('Error: {}'.format(e))
        return None

