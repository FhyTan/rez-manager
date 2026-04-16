name = "studio_core"

version = "1.1.0"

description = "Shared pipeline bootstrap package with publish and review utilities."

tools = [
    "studio-shell",
    "asset-sync",
    "publish-review",
]


def commands():
    env.PATH.append("{root}/bin")
    env.PYTHONPATH.append("{root}/python")
    env.STUDIO_PIPELINE_ROOT = "{root}"
    env.STUDIO_SHOW_CONFIG = "{root}/config/show-default.yaml"
