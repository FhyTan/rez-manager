name = "studio_core"

version = "1.0.0"

description = "Shared pipeline bootstrap package for artist workstations."

tools = [
    "studio-shell",
    "asset-sync",
]


def commands():
    env.PATH.append("{root}/bin")
    env.PYTHONPATH.append("{root}/python")
    env.STUDIO_PIPELINE_ROOT = "{root}"
