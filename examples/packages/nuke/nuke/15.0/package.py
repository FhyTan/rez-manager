name = "nuke"

version = "15.0"

description = "Foundry Nuke 15.0."

tools = [
    "nuke",
    "nukeassist",
    "nukestudio",
]


def commands():
    env.PATH.append("C:/Program Files/Nuke15.0v4")
    env.NUKE_PATH.append("{root}/plugins")
