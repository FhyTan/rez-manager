name = "shot_tools"

version = "2.4.0"

description = "Shot assembly and publish tools shared across departments."

requires = [
    "studio_core-1.1+<2",
    "usd-24+<25",
]

tools = [
    "shot-open",
    "shot-publish",
    "shot-validate",
]


def commands():
    env.PATH.append("{root}/bin")
    env.PYTHONPATH.append("{root}/python")
    env.STUDIO_SHOT_TEMPLATE = "episodic"
