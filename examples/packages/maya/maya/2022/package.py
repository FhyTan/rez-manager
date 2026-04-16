name = "maya"

version = "2022"

description = "Autodesk Maya 2022"

tools = [
    "maya",
    "mayapy",
    "mayabatch",
]


def commands():
    env.PATH.append("C:/Program Files/Autodesk/Maya2022/bin")
