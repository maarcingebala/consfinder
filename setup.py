#!/usr/bin/env python
# coding: utf-8

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='Consfinder',
    version='0.0.1',
    description='''A tool for measuring the inconsistency of knowledge
        and determining a consenus''',
    author='Marcin Gębala',
    author_email='maarcin.gebala@gmail.com',
    packages=['consfinder',],
    entry_points={
        'console_scripts': [
            'consfinder = consfinder.app:main',
        ]
    }
 )