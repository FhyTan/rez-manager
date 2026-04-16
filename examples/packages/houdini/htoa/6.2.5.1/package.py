name = "htoa"

version = "6.2.5.1"

description = "Houdini to Arnold integration package."

requires = [
    "houdini-20.0+<21",
    "arnold-7.3+<8",
]


def commands():
    env.HOUDINI_PATH.append("{root}/htoa")
    env.HTOA_PLUGIN_PATH.append("{root}/htoa")
