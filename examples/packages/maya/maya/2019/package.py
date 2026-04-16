name = "maya"

version = "2019"

description = "Autodesk Maya 2019"

tools = [
    "maya",
    "mayapy",
    "mayabatch",
]


def commands():
    env.PATH.append("C:/Program Files/Autodesk/Maya2019/bin")
