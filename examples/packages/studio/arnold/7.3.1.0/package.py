name = "arnold"

version = "7.3.1.0"

description = "Arnold renderer core package for DCC integrations."

tools = [
    "kick",
    "maketx",
    "oiiotool",
]


def commands():
    env.PATH.append("{root}/bin")
    env.ARNOLD_PLUGIN_PATH.append("{root}/plugins")
