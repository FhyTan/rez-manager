# -*- coding: utf-8 -*-

name = 'idna'

version = '3.11'

description = \
    """
    Internationalized Domain Names in Applications (IDNA)
    """

variants = [['python-3.12']]

def commands():
    env.PYTHONPATH.append('{root}/python')

timestamp = 1776322912

hashed_variants = True

from_pip = True

is_pure_python = True

pip_name = 'idna (3.11)'

format_version = 2
