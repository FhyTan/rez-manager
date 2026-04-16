name = "nukex"

version = "15.0"

description = "Foundry NukeX feature set for Nuke 15.0."

requires = [
    "nuke-15.0",
]

tools = [
    "nuke",
    "hiero",
]


def commands():
    env.NUKE_PATH.append("{root}/plugins")
    env.NUKE_ENABLE_LEGACY_X = "0"
