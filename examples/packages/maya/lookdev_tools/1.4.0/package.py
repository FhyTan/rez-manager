name = "lookdev_tools"

version = "1.4.0"

description = "Lookdev helpers for shader publishing and turntable generation."

requires = [
    "maya-2024+<2026",
    "mtoa-5.5+<6",
    "ocio-2.3+<3",
    "studio_core-1.1+<2",
]

tools = [
    "shader-publish",
    "turntable-submit",
]


def commands():
    env.PYTHONPATH.append("{root}/python")
    env.MAYA_SCRIPT_PATH.append("{root}/scripts")
