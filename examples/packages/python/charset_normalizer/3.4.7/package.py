# -*- coding: utf-8 -*-

name = 'charset_normalizer'

version = '3.4.7'

description = \
    """
    The Real First Universal Charset Detector. Open, modern and actively maintained alternative to Chardet.
    """

tools = ['normalizer.exe']

variants = [['platform-windows', 'arch-AMD64', 'python-3.12']]

def commands():
    env.PYTHONPATH.append('{root}/python')
    env.PATH.append('{root}/bin')

timestamp = 1776322912

hashed_variants = True

from_pip = True

is_pure_python = False

pip_name = 'charset-normalizer (3.4.7)'

format_version = 2
