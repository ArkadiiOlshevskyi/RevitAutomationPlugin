import os.path
import sys
import clr
import json
import inspect
import logging
import datetime
import traceback

################## Opening JSON from backend with paths to files to convert ##################
json_file_path = "~\\target_file.json"
with open(json_file_path, 'r') as json_file:
    data = json_file.read()
data_from_target_json = json.loads(data)
client = data_from_target_json['project_info']['client']
input_fml_file = data_from_target_json['paths']['input_fml']
input_ifc_file = data_from_target_json['paths']['input_ifc']
input_raw_rvt_file = data_from_target_json['paths']['input_rvt_raw']
output_path = data_from_target_json['paths']['output']
paper_size = data_from_target_json['printing']['paper_size']
paper_orientation = data_from_target_json['printing']['paper_orientation']

################## importing revit and C# modules ##################
sys.path.append('C:\Program Files\IronPython 3.4\Lib\site-packages')
sys.path.append(r'C:\ifc2dwg')
sys.path.append(r'C:\revit_automation')
sys.path.append(r'C:\Program Files\IronPython 3.4\Lib\site-packages')
sys.path.append(r'C:\Program Files\IronPython 3.4\Lib\site-packages\revit_automation_0.1')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference('RevitServices')
clr.AddReference("System.Core")
from System.Collections.Generic import List
from System.Collections.Generic import HashSet
from collections import OrderedDict
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog, RevitCommandId
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.IFC import *
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.ApplicationServices import *
from Autodesk.Revit.DB import PDFExportOptions
from Autodesk.Revit.DB.Structure import StructuralType

################## importing revit and C# modules ##################
from revit_helpers.export_dwg import *
from revit_helpers.save_to_rvt import save_project_to_rtv
from revit_helpers.export_ifc import *
from utilities.zipper import *
from revit_processor.select_door_symbol import *
from revit_processor.select_window_symbol import *
from ifc_processor.get_ifc_model_face import *
from ifc_processor.get_ifc_high_parameter import *
from ifc_processor.get_ifc_width_parameter import *
from revit_processor.convert_to_revit_units import *
from utilities.get_project_name import *
from utilities.get_floor_number_ifc import *
from json_processor.label_class import *
from json_processor.dimension_class import *
from json_processor.area_class import *
from json_processor.surface_class import *

################## FML opening data ##################
fml_input_path = input_fml_file
with open(fml_input_path, 'r') as fml_file:
    fml_data = json.load(fml_file)

################## Mapping Correct Floor Number ##################
project_name = get_project_name_from_path(fml_input_path)
floor_number = get_floor_number(input_raw_rvt_file)

def log_file_init(log_file_name):
    """
    Function to create or initialize the log file (Python 2.7 running in pyRevit backend).
    @param log_file_name: The path to the log file
    @return: None
    """
    try:
        if not os.path.exists(log_file_name):
            open(log_file_name, 'w').close()
        if os.path.exists(log_file_name):
            msg = 'Successfully created LOG file -> {}'.format(log_file_name)
            logging.info(msg)
            return log_file_name
        else:
            msg = 'Log file not created -> {}'.format(log_file_name)
            logging.error(msg)
    except Exception as e:
        msg = 'Failed to initialize log file -> {}'.format(e)
        logging.error(msg)


def log_message(log_file_name, message, is_error=False):
    """
    Function to write logs to the txt file (Python 2.7 running in pyRevit backend).
    @param log_file_name: The path to the log file
    @param message: The log message to write
    @param is_error: Flag to indicate if the message is an error
    @return: None
    """
    try:
        frame = inspect.currentframe().f_back
        function_name = frame.f_code.co_name
        line_number = frame.f_lineno
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = '{} - Function: {} - Line: {} - {}'.format(timestamp, function_name, line_number, message)
        with open(log_file_name, 'a') as log_file:
            log_file.write(log_entry + '\n')
        if is_error:
            logging.error(log_entry)
        else:
            logging.info(log_entry)
    except Exception as e:
        msg = 'Failed to write to log file -> {}'.format(e)
        logging.error(msg)


def log_exception(log_file_name, e):
    """
    Function to log exception details.
    @param log_file_name: The path to the log file
    @param e: The exception object
    @return: None
    """
    error_message = traceback.format_exc()  # Get detailed error information
    log_message(log_file_name, 'Exception occurred: {}'.format(error_message), is_error=True)

    log_txt_file_name = os.path.join(output_path, "{}_AutoPlan_Convert_log.txt".format(project_name))
    logging.basicConfig(filename=log_txt_file_name, level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    log_file_init(log_txt_file_name)
    log_message(log_txt_file_name, "Converting RawRevit => PDF | AutoCad | Img.")  # Write a log message

    try:
        doc = __revit__.OpenAndActivateDocument(input_raw_rvt_file)
        rvt_document_active = __revit__.ActiveUIDocument.Document  # uncomment in Revit python shell test
        rvt_document = rvt_document_active
        if doc:
            msg = 'Document opened and activated: {}'.format(rvt_document_active.Title)
            log_message(log_txt_file_name, msg)
        else:
            msg = 'Failed to open the document: {}'.format(input_raw_rvt_file)
            log_message(log_txt_file_name, msg)
    except Exception as e:
        log_exception(log_txt_file_name, e)
