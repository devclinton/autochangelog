#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script for the autochangelog"""
import sys

from setuptools import setup, find_packages


with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read().split("\n")

build_requirements = ['flake8', 'coverage', 'py-make', 'bump2version', 'twine']
setup_requirements = []
test_requirements = ['pytest', 'pytest-runner', 'pytest-timeout', 'pytest-cache'] + build_requirements

extras = dict(test=test_requirements, packaging=build_requirements)

authors = [
    ("Clinton Collins", "ccollins@idmod.org")
]

setup(
    author=[author[0] for author in authors],
    author_email=[author[1] for author in authors],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Tool to autogenerate changelogs",
    install_requires=requirements,
    long_description=readme,
    include_package_data=True,
    keywords='changelog, automation, build, versioning',
    name='autochangelog',
    packages=find_packages(),
    python_requires='>=3.6.*',
    setup_requires=setup_requirements,
    test_suite='tests',
    entry_points={
        "console_scripts": ["autochangelog=autochangelog.cli:cli"],
        "autochangelog.cli_src_plugins":
            [
                "git=autochangelog.gitlog_source:git",
                "github=autochangelog.github_issues_source:github",
                "json=autochangelog.json_output:json",
                "markdown=autochangelog.markdown_output:markdown"
            ]
    },
    extras_require=extras,
    version='0.0.1-dev'
)
