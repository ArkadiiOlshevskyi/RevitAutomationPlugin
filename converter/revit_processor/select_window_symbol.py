import logging
import inspect
from Autodesk.Revit.DB import *

logger = logging.getLogger(__name__)


def select_window_symbol(active_document, ifc_family_name, default_family_symbol):
    """
    Mapping Function to select PreLoaded WINDOW families in Revit rvt_document.
    if Symbol is not found - uses Default symbol for this category(OST_Windows)
    
    Parameters:
    active_document (Document): The active Revit document.
    active_document (str): IFC family project_name like "Window_218 2090".
    default_window_family_symbol (str): Name of Default model to find PreLoaded in Revit model.

    Returns:
    Family(Window_218) or Default Family
    
    Raises:
    Exception: If there is an error during activation, the transaction is
               rolled back and the error is logged.
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Selecting prev Loaded Family Symbol -> {}'.format(function_name))
    print('Selecting prev Loaded Family Symbol -> {}'.format(function_name))

    param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
    f_param = ParameterValueProvider(param_id)
    f_evaluator = FilterStringEquals()
    f_rule = FilterStringRule(f_param, f_evaluator, ifc_family_name)
    filter_symbol_name = ElementParameterFilter(f_rule)

    try:
        selected_family_symbols = FilteredElementCollector(active_document) \
            .OfCategory(BuiltInCategory.OST_Windows) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()

        if selected_family_symbols is not None:
            return selected_family_symbols

        print("Symbol '{}' not found.".format(ifc_family_name))
        print("Using Default Symbol -> '{}'".format(default_family_symbol))
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

    except Exception as e:
        print('Error while selecting preloaded family_symbol symbol-> {}'.format(e))
        logger.error('Error while selecting preloaded family_symbol symbol-> {}'.format(e))
        return None
