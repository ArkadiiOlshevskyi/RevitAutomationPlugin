import os
import inspect
import logging
import zipfile

logger = logging.getLogger(__name__)


def make_zip(output_path, zip_file_name, extensions):
    """
    Making zip file in OUTPUT folder from project files like:
    ".fml", ".rvt", ".dwg", ".dxf", ".dfx", ".3ds",
    ".ifc", ".pcp", ".dxf", ".mtl", ".fbx", ".stl", ".obj"
    """
    function_name = inspect.currentframe().f_code.co_code
    logging.info('Trying to zip project files in ZIP archive...')

    try:
        if os.path.exists(output_path):
            with zipfile.ZipFile(os.path.join(output_path, zip_file_name + '.zip'), 'w', zipfile.ZIP_DEFLATED) as zip:
                files_to_zip = []
                for file in os.listdir(output_path):
                    if file == zip_file_name + '.zip':
                        files_to_zip.append(file)  # Skip the zip file itself
                    elif any(file.startswith(zip_file_name) and file.endswith(ext) for ext in extensions):
                        zip.write(os.path.join(output_path, file), file)
                logging.info('ZIP was created in OUTPUT folder')
    except Exception as e:
        logging.error('Error -> {}'.format(e))
