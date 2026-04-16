name = "scene_assembly"

version = "2.1.0"

description = "Scene assembly helpers for shot layout and cache updates."

requires = [
    "maya-2023+<2026",
    "studio_core-1.0+<2",
]

tools = [
    "scene-assembly",
    "cache-repath",
]


def commands():
    env.PYTHONPATH.append("{root}/python")
    env.MAYA_SCRIPT_PATH.append("{root}/scripts")
