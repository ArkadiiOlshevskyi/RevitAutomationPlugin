import logging
import inspect
from Autodesk.Revit.DB import ElementId, BuiltInParameter, ParameterValueProvider, FilterStringEquals, FilterStringRule, \
    ElementParameterFilter, FilteredElementCollector
from Autodesk.Revit.DB import Document, FilteredElementCollector, ElementId, BuiltInCategory

logger = logging.getLogger(__name__)


def select_door_symbol(document, family_name, default_family_symbol):
    """
    Function to select Loaded DOOR families in Revit rvt_document
    And Activate them, so we can use them Symbols to Family Creation
    RETURNS Family
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Selecting prev Loaded Family Symbol -> {}'.format(function_name))
    print('Selecting prev Loaded Family Symbol -> {}'.format(function_name))

    param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
    f_param = ParameterValueProvider(param_id)
    f_evaluator = FilterStringEquals()
    f_rule = FilterStringRule(f_param, f_evaluator, family_name)
    filter_symbol_name = ElementParameterFilter(f_rule)

    try:
        selected_family_symbols = FilteredElementCollector(document) \
            .OfCategory(BuiltInCategory.OST_Doors) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()

        if selected_family_symbols is not None:
            return selected_family_symbols

        print("Symbol '{}' not found.".format(family_name))
        print("Using Default Symbol -> '{}'".format(default_family_symbol))
        logger.info("Using Default Symbol -> '{}'".format(default_family_symbol))

        param_id = ElementId(BuiltInParameter.SYMBOL_NAME_PARAM)  # Use the parameter for symbol project_name
        f_param = ParameterValueProvider(param_id)
        f_evaluator = FilterStringEquals()
        f_rule = FilterStringRule(f_param, f_evaluator, default_family_symbol)
        filter_symbol_name = ElementParameterFilter(f_rule)

        default_selection = FilteredElementCollector(document) \
            .OfCategory(BuiltInCategory.OST_Doors) \
            .WherePasses(filter_symbol_name) \
            .WhereElementIsElementType() \
            .FirstElement()

        return default_selection

    except Exception as e:
        print('Error while selecting preloaded family_symbol symbol-> {}'.format(e))
        logger.error('Error while selecting preloaded family_symbol symbol-> {}'.format(e))
        return None
