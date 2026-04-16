name = "maya"

version = "2024"

description = "Autodesk Maya 2024"

tools = [
    "maya",
    "mayapy",
    "mayabatch",
]


def commands():
    env.PATH.append("C:/Program Files/Autodesk/Maya2024/bin")
