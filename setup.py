#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import os
import sys
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install


if sys.version_info < (3, 6, 4):
    print("Python version 3.6.4 or superior is required for use with app")
    raise SystemExit(1)


def local_file(*f):
    with open(os.path.join(os.path.dirname(__file__), *f), "r") as fd:
        return fd.read()


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        # PUT YOUR POST-INSTALL SCRIPT HERE or CALL A FUNCTION
        install.run(self)


class VersionFinder(ast.NodeVisitor):
    VARIABLE_NAME = "version"

    def __init__(self):
        self.version = None

    def visit_Assign(self, node):
        try:
            if node.targets[0].id == self.VARIABLE_NAME:
                self.version = node.value.s
        except Exception:
            pass


def read_version():
    finder = VersionFinder()
    finder.visit(ast.parse(local_file("shortage", "version.py")))
    return finder.version


install_requires = [
    "flask>=1.1",
    "requests>=2.22",
    "authlib>=0.11.0",
    "chemist>=1.5",
    "twilio>=6.29",
    "flask-restplus>=0.12.1",
    "pendulum>=2.0",
    "click>=7.0",
    "coloredlogs>=10.0",
    "pip>=19.2",
    "pync>=2.0",
]

tests_require = [
]


setup(
    name="shortage-app",
    version=read_version(),
    description="\n".join(
        [
            "Shortage is an SMS service."
        ]
    ),
    long_description=local_file("README.rst"),
    entry_points={"console_scripts": ["shortage = shortage.cli:shortage"]},
    url="https://github.com/gabrielfalcao/shortage-app",
    packages=find_packages(exclude=["*tests*"]),
    include_package_data=True,
    package_data={"shortage": "README.rst *.png shortage/*.png *.rst docs/* docs/*/*".split()},
    zip_safe=False,
    author="Shortage Inc.",
    author_email="dev@shortage.com",
    install_requires=install_requires,
    extras_require={"tests": tests_require},
    tests_require=tests_require,
    dependency_links=[],
)
