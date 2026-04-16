name = "houdini"

version = "19.5"

description = "SideFX Houdini 19.5."

tools = [
    "houdini",
    "hython",
    "husk",
]


def commands():
    env.PATH.append("C:/Program Files/Side Effects Software/Houdini 19.5/bin")
    env.HFS = "C:/Program Files/Side Effects Software/Houdini 19.5"
