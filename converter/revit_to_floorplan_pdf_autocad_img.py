import os.path
import sys
import clr
import json
import logging

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

################## FML openig data ##################
fml_input_path = input_fml_file
with open(fml_input_path, 'r') as fml_file:
    fml_data = json.load(fml_file)

################## Initialize Revit Document ##################
try:
    doc = __revit__.OpenAndActivateDocument(input_raw_rvt_file)
    rvt_document_active = __revit__.ActiveUIDocument.Document  # uncomment in Revit python shell test
    rvt_document = rvt_document_active
    if doc:
        logger.info('Document opened and activated: {}'.format(rvt_document_active.Title))
    else:
        logger.info('Failed to open the document: {}'.format(input_raw_rvt_file))
except Exception as e:
    logger.info('Error occurred -> {}'.format(e))

################## Mapping Correct Floor Number ##################
project_name = get_project_name_from_path(fml_input_path)
floor_number = get_floor_number(input_raw_rvt_file)

######################### Selecting all symbols in revit project ann trying to activate them ##########################
all_element_types = FilteredElementCollector(rvt_document). \
    WhereElementIsElementType(). \
    ToElements()
t = Transaction(rvt_document, "Activating Symbols")
for element in all_element_types:
    try:
        t.Start()
        element.Activate()
        t.Commit()
    except Exception as e:
        t.RollBack()
        logging.error('Cannot Activate ->{}'.format(e))
        pass

########################### Selecting view plan ###########################
all_levels = FilteredElementCollector(rvt_document).OfClass(Level).WhereElementIsNotElementType().ToElements()
if not all_levels:
    raise ValueError("No levels found in the project")
selected_level = all_levels[0]
selected_level_name = selected_level.Name
all_plans = FilteredElementCollector(rvt_document).OfClass(ViewPlan).WhereElementIsNotElementType().ToElements()
selected_view_plan = None
for plan in all_plans:
    plan_name = plan.Name
    if plan_name == selected_level_name:
        selected_view_plan = plan
        break
if selected_view_plan:
    try:
        if selected_view_plan.Document == rvt_document:
            uiapp = __revit__
            app = uiapp.Application
            uidoc = uiapp.ActiveUIDocument
            uidoc.ActiveView = selected_view_plan
        else:
            logging.info('Selected view does not belong to the current document.'.format())
    except Exception as e:
        logging.info('Error in activating view -> {}'.format(e))
else:
    logging.info('No matching view plan found')

########################### Mapping walls in plan to Black color ###########################
# Getting all fill patterns
all_fills = FilteredElementCollector(rvt_document).OfClass(
    FillPatternElement).WhereElementIsNotElementType().ToElements()
solid_fill_id = None
for fill in all_fills:
    fill_name = fill.Name
    if fill_name == "<Solid fill>":
        solid_fill_id = fill.Id
        logging.info('Found -> {}'.format(fill_name))
        break
if solid_fill_id is None:
    raise Exception("Solid fill pattern not found")
# Getting all visible walls
all_walls = FilteredElementCollector(rvt_document).OfClass(Wall).ToElements()
logging.info('Number of walls found: {}'.format(len(all_walls)))
t = Transaction(rvt_document, "Changing fill of walls")
try:
    for wall in all_walls:
        wall_type_id = wall.GetTypeId()
        wall_type = rvt_document.GetElement(wall_type_id)
        wall_type_parameters = wall_type.Parameters
        selected_parameter = None
        for p in wall_type_parameters:
            parameter_name = p.Definition.Name
            if parameter_name == 'Coarse Scale Fill Pattern':
                selected_parameter = p
        t.Start()
        selected_parameter.Set(solid_fill_id)
        t.Commit()
        logging.info("Fill pattern changed successfully")
except Exception as e:
    t.RollBack()
    logging.info(e)

########################### Mapping text from FML ###########################
for floor in fml_data['floors']:
    if floor['level'] == floor_number:
        for design in floor['designs']:
            for labels in design['labels']:
                new_label = Label.process_config(labels)
                logging.info('Found -> {}'.format(new_label))
                label_text = new_label.text
                x = x_revit(new_label.x)
                y = y_revit(new_label.y)
                text_rotation_value = rotation_label_revit(new_label.rotation)
                # Select all text styles (TextNoteType objects)
                all_text_styles = FilteredElementCollector(rvt_document). \
                    OfClass(TextNoteType). \
                    WhereElementIsElementType(). \
                    ToElements()
                text_selected = None
                for text_style in all_text_styles:
                    text_style_name = text_style.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
                    if text_style_name == '3du_text_2mm':
                        text_selected = text_style
                        logging.info('Matched -> {}'.format(
                            text_selected.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()))
                        break
                if not text_selected:
                    raise ValueError("Text style '3du_text_2mm' not found.")
                logging.info('Selected Text -> {}'.format(text_selected))
                # Creating a new text(Label)
                t = Transaction(rvt_document, 'Create Text')
                try:
                    t.Start()
                    view = selected_view_plan
                    origin = XYZ(x, y, 0)
                    origin_z = XYZ(x, y, 10)
                    text_rotation_Z_axis = Line.CreateBound(origin, origin_z)
                    new_text = TextNote.Create(rvt_document, view.Id, origin, label_text, text_selected.Id)
                    text_element_rotated = new_text.Location.Rotate(text_rotation_Z_axis, text_rotation_value)
                    t.Commit()
                    logging.info('Text created -> {} {}'.format(new_text.Id, t.GetStatus()))
                except Exception as e:
                    t.RollBack()
                    logging.info('Error -> {} {}'.format(e, t.GetStatus()))

########################### Mapping dimension from FML ###########################
selected_dimension_type = None
target_dimension_name = "3du dim_Linear_2.25mm"  # preloaded dimension for template

# Selecting Dimension type
all_dimension_types = FilteredElementCollector(rvt_document). \
    OfClass(DimensionType). \
    WhereElementIsElementType(). \
    ToElements()

for dim_type in all_dimension_types:
    try:
        param = dim_type.LookupParameter('Type Name')
        if param:
            dim_name = param.AsString()
            if dim_name == target_dimension_name:
                selected_dimension_type = dim_type
                logging.info('Found -> Selected Dimension Type Name -> {}'.format(selected_dimension_type.Name))
                logging.info('Selected Dimension Type -> type {}'.format(type(selected_dimension_type)))  # type <class 'str'>
                break
    except Exception as e:
        logging.info('Error in accessing dimension type name -> {}'.format(e))

# Extraction dimension data from FML
for floor in fml_data['floors']:
    if floor['level'] == floor_number:
        for design in floor['designs']:
            for dimensions in design['dimensions']:
                new_dimension = Dimension.process_config(dimensions)
                logging.info('Found -> {}'.format(new_dimension))
                dimension_text = new_dimension.dimension_type
                ax = x_revit(new_dimension.ax)
                ay = y_revit(new_dimension.ay)
                bx = x_revit(new_dimension.bx)
                by = y_revit(new_dimension.by)
                Z_coordinate = 0
                point_a_dim_line = XYZ(ax, ay, Z_coordinate)
                point_b_dim_line = XYZ(bx, by, Z_coordinate)
                t = Transaction(rvt_document, 'Create Dimension')
                try:
                    t.Start()
                    # Create a line for the dimension
                    line = Line.CreateBound(point_a_dim_line, point_b_dim_line)
                    curve_element = rvt_document.Create.NewDetailCurve(selected_view_plan, line)
                    # Collect the references from the endpoints of the line
                    references = ReferenceArray()
                    references.Append(curve_element.GeometryCurve.GetEndPointReference(0))
                    references.Append(curve_element.GeometryCurve.GetEndPointReference(1))
                    # Create the dimension
                    dimension = rvt_document.Create.NewDimension(selected_view_plan,
                                                                 line,
                                                                 references,
                                                                 selected_dimension_type)
                    t.Commit()
                    logging.info('Dimension created -> {} {}'.format(dimension, t.GetStatus()))
                except Exception as e:
                    t.RollBack()
                    logging.info('Error -> {} {}'.format(e, t.GetStatus()))

########################### Cropping the ViewPlan in viewport ###########################
# Preparing the lists for points to crop the view
all_x = []
all_y = []

# Get all dimensions in view to crop the view from points
all_dim_in_model = FilteredElementCollector(rvt_document). \
    OfCategory(BuiltInCategory.OST_Dimensions). \
    WhereElementIsNotElementType(). \
    ToElements()

# getting points from dimensions by parsing BoundingBox XYZ form selected ViewPlan
for dim in all_dim_in_model:
    dim_bbox = dim.get_BoundingBox(selected_view_plan)
    dim_bbox_Min = dim_bbox.Min
    dim_bbox_Max = dim_bbox.Max
    dim_bbox_max_x = dim_bbox_Max.X
    dim_bbox_max_y = dim_bbox_Max.Y
    dim_bbox_min_x = dim_bbox_Min.X
    dim_bbox_min_y = dim_bbox_Min.Y
    all_x.append(dim_bbox_max_x)
    all_x.append(dim_bbox_min_x)
    all_y.append(dim_bbox_max_y)
    all_y.append(dim_bbox_min_y)

# Step 2 - Get all walls in the active document
all_walls = FilteredElementCollector(rvt_document) \
    .OfCategory(BuiltInCategory.OST_Walls) \
    .WhereElementIsNotElementType() \
    .ToElements()

# Put all points from walls to a list
points_walls = []
for wall in all_walls:
    location = wall.Location
    curve = location.Curve
    points = curve.Tessellate()
    a_point = points[0]
    b_point = points[1]
    points_walls.append(a_point)
    points_walls.append(b_point)
for point in points_walls:
    x_coordinate = point.X
    all_x.append(x_coordinate)
    y_coordinate = point.Y
    all_y.append(y_coordinate)

# Setting up offset value and preparing coordinates
offset_value = 1.1
x_max = max(all_x) * offset_value
x_min = min(all_x) * offset_value
y_max = max(all_y) * offset_value
y_min = min(all_y) * offset_value

# Accessing to CropBox bounding box of VewPlan to crop it
crop_box = selected_view_plan.CropBox
crop_box_min = crop_box.Min
crop_box_max = crop_box.Max
crop_box_min_x = crop_box_min.X
new_crop_box_min = XYZ(x_min, y_min, crop_box_min.Z)
new_crop_box_max = XYZ(x_max, y_max, crop_box_max.Z)

t = Transaction(rvt_document, "Cropping View")
try:
    t.Start()
    crop_box.Min = new_crop_box_min
    crop_box.Max = new_crop_box_max
    selected_view_plan.CropBox = crop_box
    selected_view_plan.CropBoxActive = True
    selected_view_plan.CropBoxVisible = False

    # Adjusting Annotation Crop offset
    crop_region_shape_manager = selected_view_plan.GetCropRegionShapeManager()
    annotation_offset_value = 0.0102
    # Set new values for annotation crop offsets
    crop_region_shape_manager.LeftAnnotationCropOffset = annotation_offset_value
    crop_region_shape_manager.RightAnnotationCropOffset = annotation_offset_value
    crop_region_shape_manager.TopAnnotationCropOffset = annotation_offset_value
    crop_region_shape_manager.BottomAnnotationCropOffset = annotation_offset_value
    t.Commit()
    logging.info('Transaction committed successfully.'.format(t.GetStatus()))
    logging.info('Bounding box updated to Min: {} Max: {}'.format(crop_box.Min, crop_box.Max))
except Exception as e:
    t.RollBack()
    logging.exception('Transaction failed: {}'.format(e))

########################### Hiding reference plans in the selected view plan ###########################
try:
    t = Transaction(rvt_document, "Hiding Reference Plans")
    t.Start()
    # Collect all reference planes
    all_visible_reference_plans_on_viewplan = FilteredElementCollector(rvt_document).OfClass(
        ReferencePlane).WhereElementIsNotElementType().ToElements()
    if not all_visible_reference_plans_on_viewplan:
        logging.info("No reference plans found to hide.")
    else:
        logging.info('Reference plans -> {} {}'.format(len(all_visible_reference_plans_on_viewplan),
                                                all_visible_reference_plans_on_viewplan))
    # Hide reference planes
    reference_plane_ids = List[ElementId]()
    for reference in all_visible_reference_plans_on_viewplan:
        reference_plane_ids.Add(reference.Id)
    selected_view_plan.HideElements(reference_plane_ids)
    t.Commit()
    logging.info('Success', 'Reference planes have been made invisible in the selected view. {}'.format(t.GetStatus()))

except Exception as e:
    if t.HasStarted():
        t.RollBack()
    logging.exception('Transaction failed: {}'.format(e))
    pass


########################### Mapping Areas and Surfaces from FML with RoomLabes and m2 Labes ###########################
# Utility function to convert hex color to Revit Color
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return Color(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


# utility function to find centroid
def calculate_centroid(points):
    try:
        x_sum = y_sum = z_sum = 0.0
        count = len(points)
        if count == 0:
            raise ValueError("No points provided to calculate centroid")
        for point in points:
            x_sum += point.X
            y_sum += point.Y
            z_sum += point.Z
        return XYZ(x_sum / count, y_sum / count, z_sum / count)
    except Exception as e:
        logging.exception('Error calculating centroid -> {}'.format(e))
        return None


########################### Processing Areas from FML to python class ###########################
areas_objects_items_list = []
for floor in fml_data['floors']:
    if floor['level'] == floor_number:
        for designs in floor['designs']:
            for areas in designs['areas']:
                new_item = Area.process_config(areas)
                areas_objects_items_list.append(new_item)
                print('total areas >{} {}'.format(len(areas_objects_items_list), areas_objects_items_list))

try:
    default_fill_name = "3du_fill_MaskOFF"
    fill_name_base = "CustomFilledRegionType_"
    fill_name_counter = 1
    selected_fill_type = None
    all_filled_region_types = FilteredElementCollector(rvt_document).OfClass(
        FilledRegionType).WhereElementIsElementType().ToElements()
    for filled_region_type in all_filled_region_types:
        try:
            param = filled_region_type.LookupParameter('Type Name')  # Use 'Type Name' or similar parameter name
            if param:
                fill_name = param.AsString()
                if fill_name == default_fill_name:
                    selected_fill_type = filled_region_type
                    logging.info('Found -> Selected Fill Type -> {} | {}'.format(filled_region_type, fill_name))
                    logging.info('Selected Dimension Type -> type {}'.format(type(selected_fill_type)))  # type <class 'str'>
                    break
        except Exception as e:
            logging.exception('Error in accessing Fill type name -> {}'.format(e))

    # Mapping processed areas from FML
    for area in areas_objects_items_list:

        points = area.poly
        area_color_hex = area.color
        area_name = area.name

        # Processing points to curve
        processed_points = []
        area_points = area.poly
        for p in area_points:
            x = p['x']
            y = p['y']
            z = 0  # Assuming Z is 0 for 2D coordinates
            processed_points.append(XYZ(x_revit(x), y_revit(y), z))
        points = processed_points
        logging.info('FIN Processed Area points -> {}'.format(points))

        # Calculating shifts for X and Y for labels areas and surfaces
        area_name_x = area.name_x
        area_name_y = area.name_y

        # Processing XY area/surface text coordinates to revit units
        if area_name_x is None or area_name_x == 0:
            area_name_x_processed = 0
            logging.info('Not shifting area/surface text because X -> {}'.format(area_name_x_processed))
        else:
            area_name_x_processed = x_text_revit(area_name_x)
            logging.info('Processed text X coord -> {}'.format(area_name_x_processed))
        if area_name_y is None or area_name_y == 0:
            area_name_y_processed = 0
            logging.info('Not shifting area/surface text because Y -> {}'.format(area_name_y_processed))
        else:
            area_name_y_processed = y_text_revit(area_name_y)
            logging.info('Processed text Y coord -> {}'.format(area_name_y_processed))

        # Creating points for text and m2 (center of object)
        basic_surface_text_insertion_point = calculate_centroid(points)  # Got you centroid point
        shifted_xy_text_point = XYZ(basic_surface_text_insertion_point.X + area_name_x_processed,
                                    (basic_surface_text_insertion_point.Y + 0.3 + area_name_y_processed),
                                    basic_surface_text_insertion_point.Z)
        basic_area_m2_insertion_point = XYZ(basic_surface_text_insertion_point.X + area_name_x_processed,
                                            (basic_surface_text_insertion_point.Y - 0.3 + area_name_y_processed),
                                            basic_surface_text_insertion_point.Z)

        # Create a new curve loop for each area
        area_perimeter = CurveLoop()
        for i in range(len(points)):
            start = points[i]
            end = points[(i + 1) % len(points)]
            curve = Line.CreateBound(start, end)
            area_perimeter.Append(curve)
        print('Created curve loop -> {}'.format(area_perimeter))
        if selected_fill_type is None:
            raise ValueError("No selected fill type found in the document.")

        # Creating New custom Fill for each room -> Increment the fill name counter to avoid duplicates
        t = Transaction(rvt_document, "Fill Zones for Areas")
        try:
            t.Start()
            start_counter = 1
            new_fill_name = fill_name_base + str(fill_name_counter)
            fill_name_counter += 1
            filled_region_type = selected_fill_type.Duplicate(new_fill_name)
            override_graphics_settings = OverrideGraphicSettings()
            area_color_rgb = hex_to_rgb(area_color_hex)
            filled_region_type.ForegroundPatternColor = area_color_rgb
            filled_region = FilledRegion.Create(rvt_document, filled_region_type.Id, rvt_document.ActiveView.Id,
                                                [area_perimeter])
            t.Commit()
        except Exception as e:
            t.RollBack()
            logging.info(''.format(t.GetStatus()))
        created_fill_name = new_fill_name
        logging.info('Created fill name -> {}'.format(created_fill_name))

        # Extraction Area value from created fill to insert it into future m2 text
        all_created_fills = FilteredElementCollector(rvt_document).OfClass(
            FilledRegion).WhereElementIsNotElementType().ToElements()
        selected_fill = None
        extracted_created_fill_area = None

        created_type_name = created_fill_name  # created_type_name = 'CustomFilledRegionType_5'
        for fill in all_created_fills:
            fill_type_id = fill.GetTypeId()
            fill_type = rvt_document.GetElement(fill_type_id)
            fill_type_name = fill_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()  # WORKS!
            logging.info('Processed type name -> {}'.format(fill_type_name))

            if fill_type_name == created_type_name:
                logging.info('Found match with Processed type name')
                selected_fill = fill
                selected_fill_area_param = selected_fill.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                selected_fill_area = selected_fill_area_param.AsDouble()
                selected_fill_area_m2 = selected_fill_area * 0.09290304
                extracted_created_fill_area = str(round(selected_fill_area_m2, 1))[:4]
                logging.info('Rounded Fill Area -> {}'.format(extracted_created_fill_area))
                break
            else:
                logging.info('Not Found Fill with -> {}'.format(created_type_name))
                pass

        # Storing TEXT / AREA m2 / XYZ point (calculate point from poly points)
        area_m2_text = extracted_created_fill_area
        area_name = area.name
        custom_text_for_area = area.customName
        base_center_point = shifted_xy_text_point

        # Creating areaM2 text for room -> AREA (transaction) + XYZ
        logging.info('Creating m2 text ->{}'.format(area_m2_text))
        show_area_label_m2_value = area.showSurfaceArea
        logging.info('Area. Show Area M2 Label(showSurfaceArea) Value: {}'.format(show_area_label_m2_value))

        if show_area_label_m2_value == True:
            t = Transaction(rvt_document, "Creating an Area m2 Text")
            try:
                t.Start()
                doc = __revit__.ActiveUIDocument.Document
                new_area_m2_label_text = TextNote.Create(rvt_document,
                                                         selected_view_plan.Id,
                                                         basic_area_m2_insertion_point,
                                                         area_m2_text,
                                                         text_selected.Id)
                t.Commit()
                logging.info('Created m2 text -> {} with status {}'.format(new_area_m2_label_text.Id, t.GetStatus()))
                created_area_m2_text = new_area_m2_label_text
            except Exception as e:
                t.RollBack()
                logging.info("Error creating m2 text: {} {}".format(e, t.GetStatus()))
                pass

            t = Transaction(rvt_document, 'Move m2 Text Notes')
            try:
                t.Start()
                text_content = created_area_m2_text.Text
                logging.info('Text m2 -> {}'.format(text_content))
                # Get the location of the text
                loc_pt = created_area_m2_text.Coord
                logging.info('Location Point -> ({}, {}, {})'.format(loc_pt.X, loc_pt.Y, loc_pt.Z))
                # Get bounding box and calculate center point
                bbox = created_area_m2_text.get_BoundingBox(selected_view_plan)
                if bbox:
                    min_pt = bbox.Min
                    max_pt = bbox.Max
                    center_pt = XYZ((min_pt.X + max_pt.X) / 2, (min_pt.Y + max_pt.Y) / 2, (min_pt.Z + max_pt.Z) / 2)
                    logging.info('Calculated Center Point -> ({}, {}, {})'.format(center_pt.X, center_pt.Y, center_pt.Z))
                    # Calculate the translation vector
                    translation_vector = loc_pt - center_pt
                    # Move the text
                    ElementTransformUtils.MoveElement(rvt_document, created_area_m2_text.Id, translation_vector)
                    logging.info('Moved m2 text "{}" from Center Point to Location Point'.format(text_content))
                else:
                    logging.info('m2 Text: {} has no bounding box.'.format(text_content))
                t.Commit()
            except Exception as e:
                t.Rollback
                logging.info('Error moving m2 texts -> {} | {}'.format(e, t.GetStatus()))
                pass
        else:
            pass

        if custom_text_for_area is None or custom_text_for_area == 0 and area_name == 0:
            pass

        # Create text for room -> customName (transaction) + XYZ
        show_area_label_value = area.showAreaLabel
        logging.info('Area label value ->{}'.format(show_area_label_value))
        if custom_text_for_area is not None and custom_text_for_area != 0 and show_area_label_value:
            logging.info("Creating customName for area")
            t = Transaction(rvt_document, "Creating an Area Text")
            try:
                t.Start()
                doc = __revit__.ActiveUIDocument.Document
                new_area_label_text = TextNote.Create(rvt_document,
                                                      selected_view_plan.Id,
                                                      base_center_point,
                                                      custom_text_for_area,
                                                      text_selected.Id)
                t.Commit()
                logging.info('Created text -> {} with status {}'.format(new_area_label_text.Id, t.GetStatus()))
                created_area_name_text = new_area_label_text
                logging.info('Created copy id -> {}'.format(created_area_name_text.Id))
            except Exception as e:
                t.RollBack()
                logging.info("Error creating text: {} {}".format(e, t.GetStatus()))
                pass

            t = Transaction(rvt_document, 'Move Text Notes')
            try:
                t.Start()
                text_content = created_area_name_text.Text
                logging.info('Text -> {}'.format(text_content))
                # Get the location of the text
                loc_pt = created_area_name_text.Coord
                logging.info('Location Point -> ({}, {}, {})'.format(loc_pt.X, loc_pt.Y, loc_pt.Z))
                # Get bounding box and calculate center point
                bbox = created_area_name_text.get_BoundingBox(selected_view_plan)
                if bbox:
                    min_pt = bbox.Min
                    max_pt = bbox.Max
                    center_pt = XYZ((min_pt.X + max_pt.X) / 2, (min_pt.Y + max_pt.Y) / 2, (min_pt.Z + max_pt.Z) / 2)
                    logging.info('Calculated Center Point -> ({}, {}, {})'.format(center_pt.X, center_pt.Y, center_pt.Z))
                    # Calculate the translation vector
                    translation_vector = loc_pt - center_pt
                    # Move the text
                    ElementTransformUtils.MoveElement(rvt_document, created_area_name_text.Id, translation_vector)
                    logging.info('Moved text "{}" from Center Point to Location Point'.format(text_content))
                else:
                    logging.info('Text: {} has no bounding box.'.format(text_content))
                t.Commit()
            except Exception as e:
                t.Rollback
                logging.info('Error moving texts -> {} | {}'.format(e, t.GetStatus()))

        if custom_text_for_area is None or custom_text_for_area == 0 and area_name == 0:
            pass

        # Creating original name
        if custom_text_for_area is None or custom_text_for_area == 0 and area_name is not None:

            logging.info("CustomName is off or empty -> Creating original Name for area")
            t = Transaction(rvt_document, "Creating an Area Text")
            try:
                t.Start()
                doc = __revit__.ActiveUIDocument.Document
                original_area_name = TextNote.Create(rvt_document,
                                                     selected_view_plan.Id,
                                                     base_center_point,
                                                     area_name,
                                                     text_selected.Id)
                t.Commit()
                logging.info('Created original Name text -> {} with status {}'.format(original_area_name.Id, t.GetStatus()))
                created_area_name_text = original_area_name
            except Exception as e:
                t.RollBack()
                logging.info("Error creating original Name creating text: {} {}".format(e, t.GetStatus()))
                pass

            t = Transaction(rvt_document, 'Move Area Text Notes')
            try:
                t.Start()
                text_content = created_area_name_text.Text
                logging.info('Text -> {}'.format(text_content))
                # Get the location of the text
                loc_pt = created_area_name_text.Coord
                logging.info('Location Point -> ({}, {}, {})'.format(loc_pt.X, loc_pt.Y, loc_pt.Z))
                # Get bounding box and calculate center point
                bbox = created_area_name_text.get_BoundingBox(selected_view_plan)
                if bbox:
                    min_pt = bbox.Min
                    max_pt = bbox.Max
                    center_pt = XYZ((min_pt.X + max_pt.X) / 2, (min_pt.Y + max_pt.Y) / 2, (min_pt.Z + max_pt.Z) / 2)
                    logging.info('Calculated Center Point -> ({}, {}, {})'.format(center_pt.X, center_pt.Y, center_pt.Z))
                    # Calculate the translation vector
                    translation_vector = loc_pt - center_pt
                    # Move the text
                    ElementTransformUtils.MoveElement(rvt_document, created_area_name_text.Id, translation_vector)
                    logging.info('Moved Area text "{}" from Center Point to Location Point'.format(text_content))
                else:
                    logging.info('Area Text: {} has no bounding box.'.format(text_content))
                t.Commit()
            except Exception as e:
                t.Rollback
                logging.info('Error Area moving texts -> {} | {}'.format(e, t.GetStatus()))

        ############################################################
        logging.info("Done mapping area and text")

except Exception as e:
    t.RollBack()
    logging.exception("Error creating filled region: {} {}".format(e, t.GetStatus()))
    logging.exception('Error -> {}'.format(e))
    pass


############################ Regenerating / Redrawing Viewports ############################
def set_view_detail_level_to_medium(view):
    """Changing Detailing level of Active Viewport to Medium"""
    try:
        # Ensure the view is a Floor Plan or Section, which supports detail levels
        if not isinstance(view, View):
            raise TypeError("The provided view is not valid.")
        t = Transaction(view.Document, "Set View Detail Level")
        t.Start()
        view.DetailLevel = ViewDetailLevel.Medium
        t.Commit()
        logging.info('{}'.format(t.GetStatus()))
    except Exception as e:
        if t.HasStarted():
            t.RollBack()


def set_view_detail_level_to_coarse(view):
    """Changing Detailing level of Active Viewport to Coarse"""
    try:
        # Ensure the view is a Floor Plan or Section, which supports detail levels
        if not isinstance(view, View):
            raise TypeError("The provided view is not valid.")
        t = Transaction(view.Document, "Set View Detail Level")
        t.Start()
        view.DetailLevel = ViewDetailLevel.Coarse
        t.Commit()
        print('{}'.format(t.GetStatus()))

    except Exception as e:
        if t.HasStarted():
            t.RollBack()
        print('Transaction rolled back due to an error.'.format())
        print('Error message:'.format(str(e)))


def regenerate_document(doc):
    """Regenerating Active viewport back and forward to update drawing lines, fills etc."""
    try:
        logging.info('Redrawing the view')
        active_view = doc.ActiveView
        current_detail_level = active_view.DetailLevel
        logging.info("Current Detail Level:", current_detail_level)
        set_view_detail_level_to_medium(active_view)
        set_view_detail_level_to_coarse(active_view)
        new_detail_level = active_view.DetailLevel
        logging.info("New Detail Level:", new_detail_level)
        logging.info('View redrawed')
    except Exception as e:
        logging.info("An error occurred:", str(e))


doc = __revit__.ActiveUIDocument.Document
regenerate_document(doc)
regenerate_document(doc)

########################### Mapping surfaces list ##############################
# Processing Surfaces that can overlay some areas from FML to python class
surfaces_objects_items_list = []
for categories in fml_data['floors']:
    for designs in categories['designs']:
        for surfaces in designs['surfaces']:
            new_item = Surface.process_config(surfaces)
            surfaces_objects_items_list.append(new_item)

# Creating FilledRegion for Surfaces
try:
    # Selecting Setting Default 3du Fill to mapp zones (surface and rooms)
    default_fill_name = "3du_fill_MaskOFF"
    fill_name_base = "CustomFilledRegionType_"
    fill_name_counter = 1
    selected_fill_type = None
    all_filled_region_types = FilteredElementCollector(rvt_document).OfClass(
        FilledRegionType).WhereElementIsElementType().ToElements()
    for filled_region_type in all_filled_region_types:
        try:
            param = filled_region_type.LookupParameter('Type Name')
            if param:
                fill_name = param.AsString()
                if fill_name == default_fill_name:
                    selected_fill_type = filled_region_type
                    break
        except Exception as e:
            logging.exception('Error in accessing Fill type name -> {}'.format(e))

    # Mapping processed surfaces from FML
    for surface in surfaces_objects_items_list:
        points = surface.poly
        surface_color_hex = surface.color
        surface_name = surface.name
        surface_Custom_Name = surface.customName
        surface_role = surface.role
        surface_name_x = surface.name_x
        surface_name_y = surface.name_y
        surface_show_SurfaceArea = surface.showSurfaceArea
        surface_show_AreaLabel = surface.showAreaLabel

        # Processing points to curve
        processed_points = []
        surface_points = surface.poly
        for p in surface_points:
            x = p['x']
            y = p['y']
            z = 0
            processed_points.append(XYZ(x_revit(x), y_revit(y), z))
        points = processed_points

        # Calculating the shifts for X and Y for labels surfaces and surfaces
        area_name_x = surface.name_x
        area_name_y = surface.name_y

        # Processing XY area/surface text coordinates to revit units
        if area_name_x is None or area_name_x == 0:
            area_name_x_processed = 0
        else:
            area_name_x_processed = x_text_revit(area_name_x)
        if area_name_y is None or area_name_y == 0:
            area_name_y_processed = 0
        else:
            area_name_y_processed = y_text_revit(area_name_y)

        # Creating points for text and m2 (center of object)
        basic_surface_text_insertion_point = calculate_centroid(points)
        # Applying Shift X and Y
        shifted_xy_text_point = XYZ(basic_surface_text_insertion_point.X + area_name_x_processed,
                                    (basic_surface_text_insertion_point.Y + 0.3 + area_name_y_processed),
                                    basic_surface_text_insertion_point.Z)

        basic_surface_m2_insertion_point = XYZ(basic_surface_text_insertion_point.X + area_name_x_processed,
                                               (basic_surface_text_insertion_point.Y - 0.3 + area_name_y_processed),
                                               basic_surface_text_insertion_point.Z)

        # Creating a new curve loop for each surface
        surface_perimeter = CurveLoop()
        for i in range(len(points)):
            start = points[i]
            end = points[(i + 1) % len(points)]
            curve = Line.CreateBound(start, end)
            surface_perimeter.Append(curve)
        if selected_fill_type is None:
            raise ValueError("No selected fill type found in the document.")

        # Creating New custom Fill for each room -> Increment the fill name counter to avoid duplicates
        t = Transaction(rvt_document, "Fill for Surface")
        try:
            t.Start()
            start_counter = 1
            new_fill_name = fill_name_base + 'surface_' + str(fill_name_counter)
            fill_name_counter += 1
            filled_region_type = selected_fill_type.Duplicate(new_fill_name)
            override_graphics_settings = OverrideGraphicSettings()
            surface_color_rgb = hex_to_rgb(surface_color_hex)
            filled_region_type.ForegroundPatternColor = surface_color_rgb
            filled_region = FilledRegion.Create(rvt_document, filled_region_type.Id, rvt_document.ActiveView.Id,
                                                [surface_perimeter])
            t.Commit()
        except Exception as e:
            t.RollBack()
        created_fill_name = new_fill_name

        # Extraction Area value from created fill to insert it into future m2 text
        all_created_surface_fills = FilteredElementCollector(rvt_document).OfClass(
            FilledRegion).WhereElementIsNotElementType().ToElements()
        selected_fill = None
        extracted_created_fill_area = None

        created_type_name = created_fill_name
        for fill in all_created_surface_fills:
            fill_type_id = fill.GetTypeId()
            fill_type = rvt_document.GetElement(fill_type_id)
            fill_type_name = fill_type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()

            if fill_type_name == created_type_name:
                selected_fill = fill
                selected_fill_area_param = selected_fill.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)
                selected_fill_area = selected_fill_area_param.AsDouble()
                selected_fill_area_m2 = selected_fill_area * 0.09290304
                extracted_created_fill_area = str(round(selected_fill_area_m2, 1))[:4]
                break
            else:
                pass

        # Storing TEXT / AREA m2 / XYZ point (calculate point from poly points) - HERE impost
        surface_m2_text = extracted_created_fill_area
        surface_name = surface.name
        surface_custom_text_for_area = surface.customName
        base_surface_center_point = basic_surface_m2_insertion_point

        # Creating surface areaM2 for room -> surface (transaction) + XYZ
        show_surface_label_m2_value = surface.showSurfaceArea
        if show_surface_label_m2_value == True:  # Check if surface area label is to be shown
            t = Transaction(rvt_document, "Creating an Surface m2 Text")
            try:
                t.Start()
                doc = __revit__.ActiveUIDocument.Document
                new_surface_m2_label_text = TextNote.Create(
                    rvt_document,
                    selected_view_plan.Id,
                    basic_surface_m2_insertion_point,
                    surface_m2_text,
                    text_selected.Id
                )
                t.Commit()
                created_surface_m2_text = new_surface_m2_label_text
            except Exception as e:
                t.RollBack()
                pass

            t = Transaction(rvt_document, 'Move m2 Text Notes')
            try:
                t.Start()
                text_content = created_surface_m2_text.Text
                loc_pt = created_surface_m2_text.Coord
                bbox = created_surface_m2_text.get_BoundingBox(selected_view_plan)
                if bbox:
                    min_pt = bbox.Min
                    max_pt = bbox.Max
                    center_pt = XYZ((min_pt.X + max_pt.X) / 2, (min_pt.Y + max_pt.Y) / 2,
                                    (min_pt.Z + max_pt.Z) / 2)
                    translation_vector = loc_pt - center_pt
                    ElementTransformUtils.MoveElement(rvt_document, created_surface_m2_text.Id,
                                                      translation_vector)
                t.Commit()
            except Exception as e:
                t.RollBack()
                pass

        # Create text for room -> customName (transaction) + XYZ
        show_surface_label_value = surface.showAreaLabel
        if surface_custom_text_for_area is not None and surface_custom_text_for_area != 0 and show_surface_label_value:
            t = Transaction(rvt_document, "Creating an Area Text")
            try:
                t.Start()
                doc = __revit__.ActiveUIDocument.Document
                new_surface_label_text = TextNote.Create(rvt_document,
                                                         selected_view_plan.Id,
                                                         shifted_xy_text_point,
                                                         surface_custom_text_for_area,
                                                         text_selected.Id)
                t.Commit()
                created_surface_name_text = new_surface_label_text
            except Exception as e:
                t.RollBack()
                pass

            t = Transaction(rvt_document, 'Move surface Text Notes')
            try:
                t.Start()
                text_content = created_surface_name_text.Text
                # Get the location of the text
                loc_pt = created_surface_name_text.Coord
                # Get bounding box and calculate center point
                bbox = created_surface_name_text.get_BoundingBox(selected_view_plan)
                if bbox:
                    min_pt = bbox.Min
                    max_pt = bbox.Max
                    center_pt = XYZ((min_pt.X + max_pt.X) / 2, (min_pt.Y + max_pt.Y) / 2,
                                    (min_pt.Z + max_pt.Z) / 2)
                    # Calculate the translation vector
                    translation_vector = loc_pt - center_pt
                    # Move the text
                    ElementTransformUtils.MoveElement(rvt_document, created_surface_name_text.Id,
                                                      translation_vector)
                t.Commit()
            except Exception as e:
                t.Rollback

        if surface_custom_text_for_area is None or surface_custom_text_for_area == 0 and surface_name == 0:
            pass

        # Creating original name
        if surface_custom_text_for_area is None or surface_custom_text_for_area == 0 and surface_name is not None:

            t = Transaction(rvt_document, "Creating an Area Text")
            try:
                t.Start()
                doc = __revit__.ActiveUIDocument.Document
                original_surface_name = TextNote.Create(rvt_document,
                                                        selected_view_plan.Id,
                                                        shifted_xy_text_point,
                                                        surface_name,
                                                        text_selected.Id)
                t.Commit()
                created_surface_name_text = original_surface_name
            except Exception as e:
                t.RollBack()
                pass

            t = Transaction(rvt_document, 'Move Area Text Notes')
            try:
                t.Start()
                text_content = created_surface_name_text.Text
                # Get the location of the text
                loc_pt = created_surface_name_text.Coord
                # Get bounding box and calculate center point
                bbox = created_surface_name_text.get_BoundingBox(selected_view_plan)
                if bbox:
                    min_pt = bbox.Min
                    max_pt = bbox.Max
                    center_pt = XYZ((min_pt.X + max_pt.X) / 2, (min_pt.Y + max_pt.Y) / 2,
                                    (min_pt.Z + max_pt.Z) / 2)
                    translation_vector = loc_pt - center_pt
                    # Move the text
                    ElementTransformUtils.MoveElement(rvt_document, created_surface_name_text.Id,
                                                      translation_vector)
                t.Commit()
            except Exception as e:
                t.Rollback

        ################################################################################################

except Exception as e:
    t.RollBack()
    pass


########################### Exporting and Saving projects #########################
def export_image_from_view_pixels(view, export_path, view_name, pixel_size):
    """
    Exports image from Revit View with specified pixel dimensions.

    @param view: The view to export.
    @param export_path: Path to save the image.
    @param view_name: Name of the view to use in the filename.
    @param pixel_size: Size of the image in pixels.
    """
    try:
        # Check if view is valid
        if not view:
            raise ValueError("Invalid view provided for export.")

        # Ensure the export path ends with a backslash
        if not export_path.endswith(os.path.sep):
            export_path += os.path.sep

        # Define the export options
        options = ImageExportOptions()
        options.ExportRange = ExportRange.SetOfViews
        options.SetViewsAndSheets([view.Id])
        options.ZoomType = ZoomFitType.FitToPage
        options.PixelSize = pixel_size  # Directly set the pixel size
        options.FilePath = export_path + view_name + '.png'
        # Export the image
        rvt_document.ExportImage(options)
    except Exception as e:
        logging.exception('Export Image, failed to export image: {}'.format(e))


view_name = selected_view_plan.Name
pixel_size = 2500
export_image_from_view_pixels(selected_view_plan, output_path, view_name, pixel_size)

########################### Save As DWG 2dPlan - select 2d view ###########################
export_project_to_dwg_2d(rvt_document, output_path, project_name, selected_view_plan)

########################### Moving plan to dedicated list #################################################
printing_task = str(paper_size + '_' + paper_orientation)
all_sheet_views = FilteredElementCollector(rvt_document).OfClass(ViewSheet).WhereElementIsNotElementType().ToElements()
for sheet in all_sheet_views:
    sheet_name = sheet.Name
    if sheet_name == printing_task:
        selected_sheet = sheet
        break
    else:
        pass

# Making the sheetView -> Active view
doc = __revit__.ActiveUIDocument.Document
uidoc.ActiveView = selected_sheet
active_sheet_view = doc.ActiveView

# Getting insertion point from frame location (or min max bounding box)
selection_list = str(paper_size + '_titleBlock_' + paper_orientation)
all_title_blocks = FilteredElementCollector(rvt_document).OfClass(FamilyInstance). \
    OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType().ToElements()
for title_block in all_title_blocks:
    title_block_name = title_block.Name
    if title_block_name == selection_list:
        selected_title_block = title_block
        # Extracting bounding Box
        title_bounding_box = selected_title_block.get_BoundingBox(active_sheet_view)
        title_bb_min_point = title_bounding_box.Min
        title_bb_max_point = title_bounding_box.Max
        view_plan_insertion_point = XYZ(
            (title_bb_min_point.X + title_bb_max_point.X) / 2,
            (title_bb_min_point.Y + title_bb_max_point.Y) / 2,
            (title_bb_min_point.Z + title_bb_max_point.Z) / 2
        )
        break
    else:
        pass

# Placing drawing viewPlan to Sheet
t = Transaction(rvt_document, "Place ViewPlan on Sheet")
try:
    t.Start()
    viewport = Viewport.Create(rvt_document, selected_sheet.Id, selected_view_plan.Id, view_plan_insertion_point)
    t.Commit()
    logging.info('ViewPlan {} placed successfully on {} -> {}.'.format(selected_view_plan.Name, selected_sheet.Name,
                                                                t.GetStatus()))
except Exception as e:
    t.RollBack()
    logging.exception('Error placing viewPlan on SheetView -> {} {}'.format(e, t.GetStatus()))

########################### Exporting PDF ###########################
selected_sheet_view_id = selected_sheet.Id
pdf_exp_options = PDFExportOptions()
pdf_exp_options.Combine = True  # automatically adding(True) .pdf to end of the file
file_name = pdf_exp_options.FileName
file_name = output_path + project_name
default_paper_format = pdf_exp_options.PaperFormat
if paper_size == 'A4':
    paper_format = pdf_exp_options.PaperFormat.ISO_A4
elif paper_size == 'A3':
    paper_format = pdf_exp_options.PaperFormat.ISO_A3
default_paper_orientation = pdf_exp_options.PaperOrientation
if paper_orientation == 'Portrait':
    new_paper_orientation = default_paper_orientation.Portrait
elif paper_orientation == 'Landscape':
    new_paper_orientation = default_paper_orientation.Landscape
default_paper_placement = pdf_exp_options.PaperPlacement
new_paper_placement = default_paper_placement.Center
pdf_exp_options.HideCropBoundaries = True
pdf_exp_options.HideReferencePlane = True
pdf_exp_options.HideScopeBoxes = True
default_zoom_type = pdf_exp_options.ZoomType
new_zoom_type = pdf_exp_options.ZoomType.FitToPage
export_quality = pdf_exp_options.ExportQuality
try:
    pdf_exp_options.FileName = project_name
    selected_views = List[ElementId]()
    selected_views.Add(selected_sheet_view_id)
    rvt_document.Export(output_path, selected_views, pdf_exp_options)
except Exception as e:
    logging.exception('Error during PDF export -> {}'.format(e))

######################### Purging Unused models form project ##########################
all_elements_is_type = FilteredElementCollector(rvt_document).WhereElementIsElementType()  # WORKS
all_elements_isnot_type = FilteredElementCollector(rvt_document).WhereElementIsNotElementType()  # WORKS
all_elements_2 = FilteredElementCollector(rvt_document).WhereElementIsNotElementType().WhereElementIsViewIndependent()
all_duct = FilteredElementCollector(rvt_document).OfCategory(
    BuiltInCategory.OST_DuctCurves).WhereElementIsNotElementType().WhereElementIsViewIndependent()
all_pipes = FilteredElementCollector(rvt_document).OfCategory(
    BuiltInCategory.OST_PipeCurves).WhereElementIsNotElementType().WhereElementIsViewIndependent()
all_profiles = FilteredElementCollector(rvt_document).OfCategory(
    BuiltInCategory.OST_ProfileFamilies).WhereElementIsNotElementType().WhereElementIsViewIndependent()
all_railings = FilteredElementCollector(rvt_document).OfCategory(
    BuiltInCategory.OST_StairsRailing).WhereElementIsNotElementType().WhereElementIsViewIndependent()
all_starts = FilteredElementCollector(rvt_document).OfCategory(
    BuiltInCategory.OST_Stairs).WhereElementIsNotElementType().WhereElementIsViewIndependent()
all_materials = FilteredElementCollector(rvt_document).OfCategory(
    BuiltInCategory.OST_Materials).WhereElementIsNotElementType().WhereElementIsViewIndependent()
all_materials_assets = FilteredElementCollector(rvt_document).OfClass(
    Material).WhereElementIsNotElementType().WhereElementIsViewIndependent()
# Purging Unused -> Combine all element collectors into a single HashSet #################################################
all_elements_set = HashSet[Element]()
all_elements_set.UnionWith(all_elements_is_type)
all_elements_set.UnionWith(all_elements_isnot_type)
all_elements_set.UnionWith(all_elements_2)
all_elements_set.UnionWith(all_duct)
all_elements_set.UnionWith(all_pipes)
all_elements_set.UnionWith(all_profiles)
all_elements_set.UnionWith(all_railings)
all_elements_set.UnionWith(all_starts)
all_elements_set.UnionWith(all_materials)
all_elements_set.UnionWith(all_materials_assets)
# Collecting all to HashSet
element_ids_set = HashSet[ElementId]()
for element in all_elements_is_type:
    element_ids_set.Add(element.Id)
# Purging Unused -> mapping elements to "unused"
empty_hashset = HashSet[ElementId]()
unused_elements = rvt_document.GetUnusedElements(empty_hashset)
# Purging Unused -> Deleting elements
t = Transaction(rvt_document, "Deleting elements")
for element in unused_elements:
    try:
        t.Start()
        rvt_document.Delete(element)
        t.Commit()
        print(t.GetStatus())
    except Exception as e:
        t.RollBack()
        logging.exception('Cannot Purge: {} {}'.format(e, t.GetStatus()))
        pass

######################## Update Final Revit ##########################
save_project_to_rtv(rvt_document, output_path, project_name)

# Removing raw revit - test on BACKEND LAUNCH
raw_revit_file_to_remove = input_raw_rvt_file
try:
    if os.path.exists(raw_revit_file_to_remove):
        os.remove(raw_revit_file_to_remove)
        print('Raw Revit file has been removed successfully! -> {}'.format(raw_revit_file_to_remove))
    else:
        print('Error: Raw Revit file does not exist!')
except Exception as e:
    logging.exception('Error with removing raw Revit file: {}'.format(e))
