#!/usr/bin/env python3
from distutils.core import setup

from db import name, version


setup(
    name=name,
    version=version,
    description='a human-readable, magic database in Python',
    license='MIT',
    author='Foster McLane',
    author_email='fkmclane@gmail.com',
    packages=['db'],
)
