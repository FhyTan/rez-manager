name = "maya_language"

version = "chinese"

description = "Chinese language resources for Maya."

requires = [
    "maya",
]


def commands():
    env.MAYA_UI_LANGUAGE = "zh_CN"
