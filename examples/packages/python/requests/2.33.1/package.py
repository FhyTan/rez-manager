# -*- coding: utf-8 -*-

name = 'requests'

version = '2.33.1'

description = 'Python HTTP for Humans.'

requires = [
    'certifi-2023.5.7+',
    'urllib3-1.26+<3',
    'idna-2.5+<4',
    'charset_normalizer-2+<4'
]

variants = [['python-3.12']]

def commands():
    env.PYTHONPATH.append('{root}/python')

timestamp = 1776322912

hashed_variants = True

from_pip = True

is_pure_python = True

pip_name = 'requests (2.33.1)'

format_version = 2
