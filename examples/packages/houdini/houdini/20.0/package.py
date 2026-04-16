name = "houdini"

version = "20.0"

description = "SideFX Houdini 20.0."

tools = [
    "houdini",
    "hython",
    "husk",
    "karma",
]


def commands():
    env.PATH.append("C:/Program Files/Side Effects Software/Houdini 20.0/bin")
    env.HFS = "C:/Program Files/Side Effects Software/Houdini 20.0"
