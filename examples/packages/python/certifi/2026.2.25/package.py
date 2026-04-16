# -*- coding: utf-8 -*-

name = 'certifi'

version = '2026.2.25'

description = \
    """
    Python package for providing Mozilla's CA Bundle.
    """

authors = ['Kenneth Reitz me@kennethreitz.com']

variants = [['python-3.12']]

def commands():
    env.PYTHONPATH.append('{root}/python')

help = [['Home Page', 'https://github.com/certifi/python-certifi']]

timestamp = 1776322912

hashed_variants = True

from_pip = True

is_pure_python = True

pip_name = 'certifi (2026.2.25)'

format_version = 2
