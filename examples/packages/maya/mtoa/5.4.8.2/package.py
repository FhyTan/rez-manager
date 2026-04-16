name = "mtoa"

version = "5.4.8.2"

description = "Maya to Arnold 5.4.8.2"

requires = ["maya"]


def commands():
    env.MAYA_MODULE_PATH.append("{root}/mtoa")
    env.MAYA_RENDER_DESC_PATH = "{root}/mtoa"
