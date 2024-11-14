from Autodesk.Revit.DB import Color


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return Color(int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
