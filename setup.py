# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pika',
    'psycopg2',
    ]

setup(
    name='tumbleweed',
    version='0.0',
    description='tumbleweed',
    long_description=README + '\n\n' + CHANGES,
    author='',
    author_email='',
    url='',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points="""\
    [console_scripts]
    tumbleweed = tumbleweed:main
    """,
    )
