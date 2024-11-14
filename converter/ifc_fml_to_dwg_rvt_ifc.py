#!/bin/env python
import logging
import os
import re
import sys
import clr
import json
import shutil
from datetime import datetime

# Opening JSON from backend with paths to files to convert
json_file_path = "~\\target_file.json"
with open(json_file_path, 'r') as json_file:
    data = json_file.read()
data_from_target_json = json.loads(data)
client = data_from_target_json['project_info']['client']
input_fml_file = data_from_target_json['paths']['input_fml']
input_ifc_file = data_from_target_json['paths']['input_ifc']
output_path = data_from_target_json['paths']['output']

# Opening JSON with templates for convert - settled fot each client individually
with open(
        "~\\revit_automation_0.1\\revit_database\\client_templates\\templates.json",
        'r') as json_file:
    data = json_file.read()
templates = json.loads(data)
settled_in_revit_ui_template_path = templates['settled_in_revit_ui']
default_revit_template_path = templates['default_client_mm']
correct_revit_template_path = None

try:
    if client in templates:
        correct_revit_template_path = templates[client]
        shutil.copyfile(correct_revit_template_path, settled_in_revit_ui_template_path)
        last_modified_timestamp = os.path.getmtime(settled_in_revit_ui_template_path)
        last_modified_date = datetime.fromtimestamp(last_modified_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    else:
        shutil.copyfile(default_revit_template_path, settled_in_revit_ui_template_path)
except Exception as e:
    pass

sys.path.append(r'C:\Program Files\IronPython 3.4\Lib\site-packages')
sys.path.append(r'C:\ifc2dwg')
sys.path.append(r'C:\revit_automation')
sys.path.append(r'C:\Program Files\IronPython 3.4\Lib\site-packages')
sys.path.append(r'C:\Program Files\IronPython 3.4\Lib\site-packages\revit_automation_0.1')
clr.AddReference(r'RevitAPI')
clr.AddReference(r'RevitAPIUI')
clr.AddReference(r'RevitServices')
clr.AddReference(r"System.Core")
from System.Collections.Generic import List
from System.Collections.Generic import HashSet
from collections import OrderedDict
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog, RevitCommandId
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.IFC import *
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.ApplicationServices import *
from Autodesk.Revit.DB.Structure import StructuralType
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
from json_processor.item_class import *
from utilities.get_project_name import *
from utilities.get_floor_number_ifc import *

# Getting data from FML
fml_input_path = input_fml_file
with open(fml_input_path, 'r') as fml_file:
    fml_data = json.load(fml_file)
ifc_input_path = input_ifc_file
project_name = get_project_name_from_path(fml_input_path)
floor_number = get_floor_number(ifc_input_path)
converted_project_name = project_name + "_" + str(floor_number)

# Setting default models to mapping
default_family_symbol = "Default_XYZ_box"
default_window_family_symbol = "window_default"
default_door_family_symbol = "door_default"

# Opening IFC file in Revit
uiapp = __revit__
app = uiapp.Application
uidoc = uiapp.ActiveUIDocument
ifc_document = app.OpenIFCDocument(ifc_input_path)


# Selecting all symbols in revit project ann trying to activate them
all_element_types = FilteredElementCollector(ifc_document). \
    WhereElementIsElementType(). \
    ToElements()
t = Transaction(ifc_document, "Activating Symbols")
for element in all_element_types:
    try:
        t.Start()
        element.Activate()
        t.Commit()
    except Exception as e:
        t.RollBack()
        logging.error('Error in Activation ->{}'.format(e))
        pass


# Mapping Windows from FML
def mapp_window_symbol(active_document, ifc_model_name, default_family_symbol):
    """
    Mapping Function to select PreLoaded WINDOW families in Revit rvt_document.
    if Symbol is not found - uses Default symbol for this category(OST_Windows)

    Parameters:
    active_document (Document): The active Revit document.
    ifc_model_name (str): IFC family project_name like "Window_218 2090".
    default_window_family_symbol (str): Name of Default model to find PreLoaded in Revit model.

    Returns:
    Family(Window_218) or Default Family

    Raises:
    Exception: If there is an error during activation, the transaction is
               rolled back and the error is logged.
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Selecting prev Loaded Family Symbol -> {}'.format(function_name))
    # Extract the base family project_name from the ifc_family_name (e.g., "Windows_208" from "Windows_208_1488")
    match = re.match(r'(Window_\d+)', ifc_model_name)
    base_family_name = match.group(1).lower()
    param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
    f_param = ParameterValueProvider(param_id)
    f_evaluator = FilterStringEquals()
    f_rule = FilterStringRule(f_param, f_evaluator, base_family_name)
    filter_symbol_name = ElementParameterFilter(f_rule)

    try:
        selected_family_symbols = FilteredElementCollector(active_document) \
            .OfCategory(BuiltInCategory.OST_Windows) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()

        if selected_family_symbols is not None:
            return selected_family_symbols
        logger.info("Using Default Symbol -> '{}'".format(default_family_symbol))
        param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
        f_param = ParameterValueProvider(param_id)
        f_evaluator = FilterStringEquals()
        f_rule = FilterStringRule(f_param, f_evaluator, default_family_symbol)
        filter_symbol_name = ElementParameterFilter(f_rule)
        default_selection = FilteredElementCollector(active_document) \
            .OfCategory(BuiltInCategory.OST_Windows) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()
        return default_selection
    except Exception as error:
        logger.error('Error while selecting preloaded family_symbol symbol-> {}'.format(error))
        return None


# Mapping Doors from FML
def mapp_door_symbol(active_document, ifc_model_name, default_family_symbol):
    """
    Mapping Function to select PreLoaded door families in Revit rvt_document.
    if Symbol is not found - uses Default symbol for this category(OST_doors)

    Parameters:
    active_document (Document): The active Revit document.
    ifc_model_name (str): IFC family project_name like "door_218 2090".
    default_door_family_symbol (str): Name of Default model to find PreLoaded in Revit model.

    Returns:
    Family(door_218) or Default Family

    Raises:
    Exception: If there is an error during activation, the transaction is
               rolled back and the error is logged.
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Selecting prev Loaded Family Symbol -> {}'.format(function_name))

    # Extract the base family project_name from the ifc_family_name (e.g., "doors_208" from "doors_208_1488")
    match = re.match(r'(Door_\d+)', ifc_model_name)
    base_family_name = match.group(1).lower()

    param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
    f_param = ParameterValueProvider(param_id)
    f_evaluator = FilterStringEquals()
    f_rule = FilterStringRule(f_param, f_evaluator, base_family_name)
    filter_symbol_name = ElementParameterFilter(f_rule)

    try:
        selected_family_symbols = FilteredElementCollector(active_document) \
            .OfCategory(BuiltInCategory.OST_Doors) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()

        if selected_family_symbols is not None:
            return selected_family_symbols
        logger.info("Using Default Symbol -> '{}'".format(default_family_symbol))

        param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
        f_param = ParameterValueProvider(param_id)
        f_evaluator = FilterStringEquals()
        f_rule = FilterStringRule(f_param, f_evaluator, default_family_symbol)
        filter_symbol_name = ElementParameterFilter(f_rule)

        default_selection = FilteredElementCollector(active_document) \
            .OfCategory(BuiltInCategory.OST_Doors) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()
        return default_selection
    except Exception as error:
        logger.error('Error while selecting preloaded family_symbol symbol-> {}'.format(error))
        return None


# Get symbol type is needed window #################################################
selection_all_ifc_windows = FilteredElementCollector(ifc_document). \
    OfCategory(BuiltInCategory.OST_Windows). \
    WhereElementIsNotElementType().ToElements()

t = Transaction(ifc_document, "Changing Window element family by ID")
for ifc_window in selection_all_ifc_windows:
    # get data from solid
    model_face = get_ifc_model_face(ifc_window)
    high_parameter = get_high_parameter(model_face)
    width_parameter = get_width_parameter(model_face)
    # mapp symbol
    window_preloaded = mapp_window_symbol(ifc_document, ifc_window.Name, default_window_family_symbol)
    window_preloaded.Activate()  # inside transaction only
    window_preloaded_id = window_preloaded.Id
    # change type, apply parameters
    t.Start()
    ifc_window.ChangeTypeId(window_preloaded_id)
    ifc_window.LookupParameter('Height').Set(high_parameter)
    ifc_window.LookupParameter('Width').Set(width_parameter)
    t.Commit()
    logging.info('Symbol is active -> {}'.format(window_preloaded.IsActive))
    logging.info(t.GetStatus())

# Get symbol type is needed doors -> Testing mapping symbols
selection_all_ifc_doors = FilteredElementCollector(ifc_document). \
    OfCategory(BuiltInCategory.OST_Doors). \
    WhereElementIsNotElementType().ToElements()

t = Transaction(ifc_document, "Changing Door element family by ID")
for ifc_door in selection_all_ifc_doors:
    # get data from solid
    model_face = get_ifc_model_face(ifc_door)
    high_parameter = get_high_parameter(model_face)
    width_parameter = get_width_parameter(model_face)
    # mapp symbol
    door_preloaded = mapp_door_symbol(ifc_document, ifc_door.Name, default_door_family_symbol)
    door_preloaded.Activate()  # inside transaction only
    door_preloaded_id = door_preloaded.Id
    # change type, apply parameters
    t.Start()
    ifc_door.ChangeTypeId(door_preloaded_id)
    ifc_door.LookupParameter('Height').Set(high_parameter)
    ifc_door.LookupParameter('Width').Set(width_parameter)
    t.Commit()
    logging.info('Symbol is active -> {}'.format(door_preloaded.IsActive))
    logging.info(t.GetStatus())


# Mapping Items from FML
def mapp_items_symbol(active_document, fml_item_name, default_family_symbol):
    """
    Mapping Function to select PreLoaded WINDOW families in Revit rvt_document.
    if Symbol is not found - uses Default symbol for this category(OST_Windows)

    Parameters:
    active_document (Document): The active Revit document.
    fml_item_name (str): Wall project_name for FML family project_name like "sd1qa2wd12es3af23rf1".
    default_window_family_symbol (str): Name of Default model to find PreLoaded in Revit model.

    Returns:
    Family(Window_218) or Default Family

    Raises:
    Exception: If there is an error during activation, the transaction is
               rolled back and the error is logged.
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Selecting prev Loaded Family Symbol -> {}'.format(function_name))

    param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
    f_param = ParameterValueProvider(param_id)
    f_evaluator = FilterStringEquals()
    f_rule = FilterStringRule(f_param, f_evaluator, fml_item_name)
    filter_symbol_name = ElementParameterFilter(f_rule)

    try:
        selected_family_symbols = FilteredElementCollector(active_document) \
            .OfCategory(BuiltInCategory.OST_GenericModel) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()
        if selected_family_symbols is not None:
            return selected_family_symbols
        logger.info("Using Default Symbol -> '{}'".format(default_family_symbol))

        param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
        f_param = ParameterValueProvider(param_id)
        f_evaluator = FilterStringEquals()
        f_rule = FilterStringRule(f_param, f_evaluator, default_family_symbol)
        filter_symbol_name = ElementParameterFilter(f_rule)
        default_selection = FilteredElementCollector(active_document) \
            .OfCategory(BuiltInCategory.OST_GenericModel) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()
        return default_selection
    except Exception as error:
        logger.error('Error while selecting preloaded family_symbol symbol-> {}'.format(error))
        return None


t = Transaction(ifc_document, "Creating New Item from FML")
try:
    for floor in fml_data['floors']:
        if floor['level'] == floor_number:
            for design in floor['designs']:
                for items in design['items']:
                    new_item = Item.process_config(items)

                    item_refid = new_item.refid
                    x = x_revit(new_item.x)
                    y = y_revit(new_item.y)
                    z = z_revit(new_item.z)
                    revit_model_XYZ_location_point = XYZ(x, y, z)
                    revit_model_length = width_revit(new_item.length)
                    revit_model_width = width_revit(new_item.width)
                    revit_model_height = height_revit(new_item.height)
                    revit_model_rotation_value = rotation_revit(new_item.rotation)
                    z_for_axis = XYZ(revit_model_XYZ_location_point.X, revit_model_XYZ_location_point.Y,
                                     revit_model_XYZ_location_point.Z + 10)
                    rotation_axis = Line.CreateBound(revit_model_XYZ_location_point, z_for_axis)
                    revit_family_symbol = mapp_items_symbol(ifc_document, item_refid, default_family_symbol)

                    t.Start()
                    new_model = ifc_document.Create.NewFamilyInstance(revit_model_XYZ_location_point,
                                                                      revit_family_symbol,
                                                                      StructuralType.NonStructural)
                    # APPLY PARAMETERS:
                    new_model.LookupParameter('Length').Set(revit_model_length)
                    new_model.LookupParameter('Width').Set(revit_model_width)
                    new_model.LookupParameter('Height').Set(revit_model_height)
                    # ROTATION FAMILY INSTANCE:
                    rotation_Z_axis = rotation_axis
                    element_rotated = new_model.Location.Rotate(rotation_Z_axis, revit_model_rotation_value)
                    t.Commit()
except Exception as e:
    logging.exception ('Error while mapping the IFC windows | You trying to mapp model that not preloaded to revit template ->{}'.format(e))
    t.RollBack()
    pass


# exporting to formats saving projects #################################################
save_project_to_rtv(ifc_document, output_path, converted_project_name)
export_project_to_dwg_3d(ifc_document, output_path, converted_project_name)

# Overwriting TargetJSON position - "input_rvt_raw": "new path for created revit file" for AutoPlan convertion
text_to_overwrite = output_path + '\\' + converted_project_name + '.rvt'
data_from_target_json['paths']['input_rvt_raw'] = text_to_overwrite
with open(json_file_path, 'w') as json_file:
    json.dump(data_from_target_json, json_file, indent=4)
with open(json_file_path, 'r') as json_file:
    data = json_file.read()
data_from_target_json = json.loads(data)
updated_revit_name = data_from_target_json['paths']['input_rvt_raw']
