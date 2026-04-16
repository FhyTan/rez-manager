name = "ocio"

version = "2.3.2"

description = "OpenColorIO configuration package for current productions."

tools = [
    "ociocheck",
    "ociochecklut",
    "ocioarchive",
]


def commands():
    env.PATH.append("{root}/bin")
    env.OCIO = "{root}/config/studio-config.ocio"
