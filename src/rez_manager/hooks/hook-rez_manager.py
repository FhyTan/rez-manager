from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files(
    "rez_manager",
    includes=[
        "data/system_env_vars.json",
        "qml/**/*.qml",
        "qml/**/qmldir",
    ],
)
