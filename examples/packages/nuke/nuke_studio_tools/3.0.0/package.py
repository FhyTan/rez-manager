name = "nuke_studio_tools"

version = "3.0.0"

description = "Review, conform, and publish tools for the compositing department."

requires = [
    "nuke-15+<16",
    "ocio-2.3+<3",
    "studio_core-1.1+<2",
]

tools = [
    "plate-publish",
    "review-publish",
]


def commands():
    env.NUKE_PATH.append("{root}/plugins")
    env.PYTHONPATH.append("{root}/python")
