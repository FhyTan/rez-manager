name = "texture_tools"

version = "2.0.0"

description = "Texture conversion and QC utilities for lookdev and surfacing."

requires = [
    "python-3.12",
    "requests-2.33.1+<3",
    "studio_core-1.1+<2",
]

tools = [
    "texture-pull",
    "texture-qc",
    "texture-publish",
]


def commands():
    env.PATH.append("{root}/bin")
    env.PYTHONPATH.append("{root}/python")
