name = "maya_language"

version = "english"

description = "English language resources for Maya."

requires = [
    "maya",
]


def commands():
    env.MAYA_UI_LANGUAGE = "en_US"
