name = "nukex"

version = "14.1"

description = "Foundry NukeX feature set for Nuke 14.1."

requires = [
    "nuke-14.1",
]

tools = [
    "nuke",
]


def commands():
    env.NUKE_PATH.append("{root}/plugins")
    env.NUKE_ENABLE_LEGACY_X = "1"
