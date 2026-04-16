name = "python"

version = "3.12"

description = "Python is a programming language that lets you work quickly and integrate systems more effectively."

tools = [
    "python",
    "pip",
]


def commands():
    env.PATH.append("path/to/python{version}")
    env.PATH.append("path/to/python{version}/Scripts")
