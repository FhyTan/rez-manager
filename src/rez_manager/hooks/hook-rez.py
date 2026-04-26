from PyInstaller.utils.hooks import collect_data_files

# Add the rezconfig.py file
datas = [
    *collect_data_files(
        "rez",
        include_py_files=True,
        includes=["rezconfig.py"],
    ),
    *collect_data_files(
        "rezplugins",
        include_py_files=True,
        includes=["**/*.py"],
    ),
]
