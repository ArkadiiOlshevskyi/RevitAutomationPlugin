import os
import sys
import json
import logging
import inspect

sys.path.append('C:\Program Files\IronPython 3.4\Lib\site-packages')

logger = logging.getLogger(__name__)


class Wall:
    """
    Wall in FML is describing the geometry.
    Wall built by Start (A) -> End (B) points * height.
    Wall can have openings (Doors and Windows)
    WAll can have material coatings
    """

    def __init__(self,
                 ax,
                 ay,
                 bx,
                 by,
                 az,
                 bz,
                 thickness,
                 balance,
                 decor_left,
                 decor_right,
                 decor_top,
                 decor_outline,
                 openings):
        self.ax = ax
        self.ay = ay
        self.bx = bx
        self.by = by
        self.az = az
        self.bz = bz
        self.thickness = thickness
        self.balance = balance
        self.decor_left = decor_left
        self.decor_right = decor_right
        self.decor_top = decor_top
        self.decor_outline = decor_outline
        self.openings = openings

    @classmethod
    def process_config(cls, wall_config):
        """Process config Wall data"""
        function_name = inspect.currentframe().f_code.co_name
        logger.info('Trying to process config Wall data in {}'.format(function_name))

        try:
            ax = wall_config['a']['x']
            ay = wall_config['a']['y']
            bx = wall_config['b']['x']
            by = wall_config['b']['y']
            az = wall_config['az']['z']
            bz = wall_config['bz']['z']
            thickness = wall_config['thickness']
            balance = wall_config['balance']
            decor_left = wall_config['decor']['left']
            decor_right = wall_config['decor']['right']
            decor_top = wall_config['decor']['top']
            decor_outline = wall_config['decor']['outline']
            openings = wall_config['openings']

            return cls(ax, ay, bx, by, az, bz, thickness, balance, decor_left, decor_right, decor_top, decor_outline,
                       openings)
        except Exception as e:
            logger.error('Error: {}, \n Function: {}'.format(e, function_name))
            return None

    def print_parsed_data(self):
        """Just a test print function"""
        print('refid: {}'.format(self.refid))
        print('refid: {}'.format(self.ax))
        print('refid: {}'.format(self.ay))
        print('refid: {}'.format(self.az))
        print('refid: {}'.format(self.bx))
        print('refid: {}'.format(self.by))
        print('refid: {}'.format(self.bz))
        print('thickness: {}'.format(self.thickness))
        print('balance: {}'.format(self.balance))
        print('decor_left: {}'.format(self.decor_left))
        print('decor_right: {}'.format(self.decor_right))
        print('decor_top: {}'.format(self.decor_top))
        print('decor_outline: {}'.format(self.decor_outline))
        print('openings: {}'.format(self.openings))


def wall_list_from_fml(input_path, project_name):  # Works Tested - not used anymore
    """
    Extracts Walls data from an FML file for a given project.

    input_path -> FML file of the project that contains all needed data
                   FML can be with extensions like '.fml' or '.json.fml'
    This list later used to create new models, geometry in revit
    by accessing Walls attributes
    """

    function_name = inspect.currentframe().f_code.co_name
    logger.info('Extracting Walls to List from FML -> {}'.format(function_name))
    walls_list = []

    try:
        for file_name in os.listdir(input_path):
            if file_name.endswith('.fml') and file_name.startswith(project_name):
                fml_to_open_path = os.path.join(input_path, file_name)
        with open(fml_to_open_path, 'r') as fml_file:
            fml_data = json.load(fml_file)
        for categories in fml_data['floors']:
            for designs in categories['designs']:
                for walls in designs['walls']:
                    new_wall = Wall.process_config(walls)
                    walls_list.append(new_wall)
        return walls_list

    except Exception as e:
        logger.error('Error: {}'.format(e))
        return None
