name = "maya"

version = "2023"

description = "Autodesk Maya 2023"

tools = [
    "maya",
    "mayapy",
    "mayabatch",
]


def commands():
    env.PATH.append("C:/Program Files/Autodesk/Maya2023/bin")
