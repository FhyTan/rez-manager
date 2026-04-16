# -*- coding: utf-8 -*-

name = 'urllib3'

version = '2.6.3'

description = \
    """
    HTTP library with thread-safe connection pooling, file post, and more.
    """

variants = [['python-3.12']]

def commands():
    env.PYTHONPATH.append('{root}/python')

timestamp = 1776322912

hashed_variants = True

from_pip = True

is_pure_python = True

pip_name = 'urllib3 (2.6.3)'

format_version = 2
