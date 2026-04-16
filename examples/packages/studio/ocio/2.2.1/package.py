name = "ocio"

version = "2.2.1"

description = "OpenColorIO configuration package for legacy shows."

tools = [
    "ociocheck",
    "ociochecklut",
]


def commands():
    env.PATH.append("{root}/bin")
    env.OCIO = "{root}/config/legacy-config.ocio"
