#!/usr/bin/python
# -*- coding: utf-8 -*-

try: import setuptools
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
from setuptools import setup

setup(
    name = 'advcashwsm',
    version = '0.0.2',
    packages = ['advcashwsm'],
    setup_requires = [
        'pysimplesoap >= 1.10'
    ]
)
