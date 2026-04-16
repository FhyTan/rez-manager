name = "solaris_bridge"

version = "0.9.0"

description = "Solaris bridge package for USD stage validation in Houdini."

requires = [
    "houdini-19.5+<21",
    "usd-24+<25",
    "studio_core-1.0+<2",
]

tools = [
    "solaris-publish",
    "solaris-validate",
]


def commands():
    env.PYTHONPATH.append("{root}/python")
    env.HOUDINI_PATH.append("{root}/houdini")
