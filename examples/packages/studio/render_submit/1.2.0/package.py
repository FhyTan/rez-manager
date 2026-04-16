name = "render_submit"

version = "1.2.0"

description = "Farm submission wrappers shared by Maya, Houdini, and Nuke."

requires = [
    "studio_core-1.1+<2",
]

tools = [
    "submit-render",
    "submit-review",
]

variants = [
    ["maya-2024+<2026"],
    ["houdini-20.0+<21"],
    ["nuke-15+<16"],
]


def commands():
    env.PATH.append("{root}/bin")
    env.STUDIO_RENDER_PRESET = "farm_default"
