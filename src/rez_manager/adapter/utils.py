import os

from rez_manager.runtime import IS_WINDOWS


def initialize_rez():
    # Ignore the user's home Rez config so the app resolves contexts from its own explicit settings.
    os.environ["REZ_DISABLE_HOME_CONFIG"] = "1"

    # This app must launch Windows commands through cmd because ResolvedContext.execute_shell does
    # not work reliably with Rez's default PowerShell path here. The launch controller therefore
    # always applies cmd-specific command wrapping on Windows instead of relying on
    # rez.system.system.shell, which only reports the OS default shell and does not reflect this
    # config override.
    if IS_WINDOWS:
        from rez.config import config  # noqa: PLC0415

        config.override("default_shell", "cmd")
