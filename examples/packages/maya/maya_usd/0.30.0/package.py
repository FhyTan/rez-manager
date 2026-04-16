name = "maya_usd"

version = "0.30.0"

description = "Maya USD plugin package for layout and lookdev exchanges."

requires = [
    "maya-2024+<2026",
    "usd-24.5+<25",
    "python-3.12",
]

tools = [
    "maya-usd-cache",
]


def commands():
    env.MAYA_MODULE_PATH.append("{root}/mayausd")
    env.PXR_PLUGINPATH_NAME.append("{root}/plugins")
