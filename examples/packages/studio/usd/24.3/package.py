name = "usd"

version = "24.3"

description = "Universal Scene Description runtime for asset interchange."

requires = [
    "python-3.11+<3.13",
]

tools = [
    "usdview",
    "usdcat",
    "usdzip",
]

variants = [
    ["python-3.11"],
    ["python-3.12"],
]


def commands():
    env.PATH.append("{root}/bin")
    env.PYTHONPATH.append("{root}/python")
    env.PXR_PLUGINPATH_NAME.append("{root}/plugins")
