import logging
import inspect
from Autodesk.Revit.DB import *

logger = logging.getLogger(__name__)


def get_ifc_model_face(element):
    """
    Getting geometrical face and store it into object
    So we can place Revit Family on it(on face instance).
    """
    function_name = inspect.currentframe().f_code.co_name
    logging.info('Trying to get IFC model geometry face...')

    try:
        options = Options()
        options.ComputeReferences = True
        options.IncludeNonVisibleObjects = False
        geometry_element = element.Geometry[options]
        for geometry_instances in geometry_element:
            geometry_instances = geometry_instances.GetInstanceGeometry()
        for solid in geometry_instances:
            get_type = solid.GetType()
        faces_list = []
        for faces in solid.Faces:
            faces_list.append(faces)
        avg_face_area = sum(faces.Area for faces in solid.Faces) / len(faces_list)
        biggest_face = []
        for big_face in faces_list:
            if big_face.Area >= avg_face_area:
                biggest_face.append(big_face)
        biggest_face_to_list = list(biggest_face)
        ifc_model_face = biggest_face_to_list[1]
        return ifc_model_face

    except Exception as e:
        logging.error('Error: {}, \n Function: {}'.format(e, function_name))
        return None
