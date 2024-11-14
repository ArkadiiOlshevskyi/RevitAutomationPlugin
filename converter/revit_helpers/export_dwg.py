import inspect
import logging
import os

import clr
from System.Collections.Generic import List
from collections import OrderedDict
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.DB.IFC import *
from Autodesk.Revit.DB import Transaction, FilteredElementCollector, View3D, DWGExportOptions, ElementId
from Autodesk.Revit.DB import *

clr.AddReference('RevitServices')
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
clr.AddReference("System")

logger = logging.getLogger(__name__)


class RoomWarningSwallower(IFailuresPreprocessor):
    def FailureHandler(self, failuresAccessor):
        fail_list = List[FailureMessageAccessor]()
        fail_acc_list = failuresAccessor.GetFailureMessages().GetEnumerator()
        for failure in fail_acc_list:
            failure_severity = failure.GetSeverity()
            if (failure_severity == FailureSeverty.Warning):
                failuresAccessor.DeleteWarning(failure)
            else:
                failuresAccessor.ResolveFailure(failure)
                return FailureProcessingResult.ProceedWithCommit
        return FailureProcessingResult.Continue


def export_project_to_dwg_3d(document,
                          output_path,
                          project_name):
    """
    Export file in revit to DWG
    It's better to export dwg in 2007 or 2013 format
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Function {} started....'.format(function_name))

    try:
        logger.info('Exporting rvt_document to DWG vers.2007....')

        t = Transaction(document, "Exporting rvt_document to DWG vers.2007....")
        t.Start()
        options = t.GetFailureHandlingOptions()
        options.SetFailuresPreprocessor(RoomWarningSwallower())
        t.SetFailureHandlingOptions(options)
        views = list(FilteredElementCollector(document).OfClass(View3D))[2]
        viewsWrap = []
        viewsWrap.Add(views.Id)
        collection = List[ElementId](viewsWrap)

        options = DWGExportOptions()
        options.FileVersion = ACADVersion.R2007
        out_name_dwg = project_name.split(".")[0] + '_3d' + ".dwg"
        document.Export(output_path, out_name_dwg, collection, options)

        t.Commit()
        logger.info('Document exported to DWG vers.2007 successfully {} \n {}'.format(out_name_dwg, t.GetStatus()))

    except Exception as e:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
            logger.error('Error exporting rvt_document to DWG vers.2007: {}'.format(e))


def export_project_to_dwg_2d(document,
                             output_path,
                             project_name,
                             viewplan):
    """
    Export file in revit to DWG
    It's better to export dwg in 2007 or 2013 format
    viewplan - is variable that contains pre-selected and activated in UI 2d floor plan
    """
    function_name = inspect.currentframe().f_code.co_name
    logger.info('Function {} started....'.format(function_name))

    try:
        logger.info('Exporting rvt_document to 2d DWG vers.2007....')

        t = Transaction(document, "Exporting rvt_document to 2d DWG vers.2007....")
        t.Start()
        options = t.GetFailureHandlingOptions()
        options.SetFailuresPreprocessor(RoomWarningSwallower())
        t.SetFailureHandlingOptions(options)
        floor_plan_view = viewplan
        viewsWrap = []
        viewsWrap.append(floor_plan_view.Id)
        collection = List[ElementId](viewsWrap)
        options = DWGExportOptions()
        options.FileVersion = ACADVersion.R2007
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        out_name_dwg = project_name.split(".")[0] + '_2d' + ".dwg"
        document.Export(output_path, out_name_dwg, collection, options)
        t.Commit()
        logger.info('Document exported to DWG vers.2007 successfully {} \n {}'.format(out_name_dwg, t.GetStatus()))

    except Exception as e:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
            logger.error('Error exporting rvt_document to DWG vers.2007: {}'.format(e))
