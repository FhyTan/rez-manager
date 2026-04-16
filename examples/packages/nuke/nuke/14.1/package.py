name = "nuke"

version = "14.1"

description = "Foundry Nuke 14.1."

tools = [
    "nuke",
    "nukeassist",
]


def commands():
    env.PATH.append("C:/Program Files/Nuke14.1v6")
    env.NUKE_PATH.append("{root}/plugins")
