name = "usd"

version = "24.5"

description = "Universal Scene Description runtime with updated Hydra tools."

requires = [
    "python-3.12",
]

tools = [
    "usdview",
    "usdcat",
    "usdrecord",
]

variants = [
    ["python-3.12"],
]


def commands():
    env.PATH.append("{root}/bin")
    env.PYTHONPATH.append("{root}/python")
    env.PXR_PLUGINPATH_NAME.append("{root}/plugins")
