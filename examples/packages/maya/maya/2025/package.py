name = "maya"

version = "2025"

description = "Autodesk Maya 2025"

tools = [
    "maya",
    "mayapy",
    "mayabatch",
]


def commands():
    env.PATH.append("C:/Program Files/Autodesk/Maya2025/bin")
