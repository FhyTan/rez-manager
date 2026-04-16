name = "mtoa"

version = "5.5.6.1"

description = "Maya to Arnold 5.5.6.1"

requires = ["maya"]


def commands():
    env.MAYA_MODULE_PATH.append("{root}/mtoa")
    env.MAYA_RENDER_DESC_PATH = "{root}/mtoa"
