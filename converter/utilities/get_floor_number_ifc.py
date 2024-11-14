import re


def get_floor_number(filename):
    try:
        match_ifc = re.search(r'_(\d+)\.ifc$', filename)
        match_rvt = re.search(r'_(\d+)\.rvt$', filename)

        if match_ifc:
            floor_number = int(match_ifc.group(1))
            return floor_number
        elif match_rvt:
            floor_number = int(match_rvt.group(1))
            return floor_number
        else:
            raise ValueError('Invalid filename format: {}'.format(filename))
    except Exception as e:
        raise
