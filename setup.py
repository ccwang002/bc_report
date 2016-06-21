import sys
import re
from os import path
from pathlib import Path
from setuptools import setup, find_packages
from codecs import open

here = path.abspath(path.dirname(__file__))


def utf8_open(*path_parts):
    return open(path.join(*path_parts), encoding='utf-8')


def find_version(*path_parts):
    with utf8_open(*path_parts) as f:
        version_match = re.search(
            r"^__version__ = ['\"]([^'\"]*)['\"]",
            f.read(), re.M
        )
    if version_match:
        return version_match.group(1)

    raise RuntimeError("Unable to find version string.")


with utf8_open("README.rst") as readme_f:
    with utf8_open("CHANGELOG.rst") as changes_f:
        long_description = readme_f.read() + '\n' + changes_f.read()

# Recursively find all files under bc_pipelines/*/{static,templates}
package_data = {}
pipelines = list(Path('bc_pipelines').iterdir())
for pipeline in pipelines:
    files = []
    for folder in ['static', 'templates']:
        files.extend(
            p.relative_to(pipeline).as_posix()
            for p in pipeline.glob('%s/**/*' % folder)
            if p.name not in ['.DS_Store'] and not p.is_dir()
        )
    package_data[pipeline.as_posix().replace('/', '.')] = files

# Define package dependencies
pkg_deps = [
    'PyYAML >= 3.11',
    'Jinja2 >= 2.8',
    'click >= 6.0',
]

if sys.platform.startswith("win32"):
    color_dep = ['colorlog[windows]']
else:
    color_dep = ['colorlog']

all_dep = []
for deps in [color_dep]:
    all_dep.extend(deps)

setup(
    name='bc_report',
    version=find_version('bc_report', '__init__.py'),

    license='MIT',
    description='BioCloud report generator',
    long_description=long_description,

    author='Liang Bo Wang',
    author_email='r02945054@ntu.edu.tw',

    url='https://github.com/ccwang002/bc_report',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    keywords='ngs',

    install_requires=pkg_deps,
    extras_require={
        ':python_version=="3.3"': ['pathlib'],
        'color': color_dep,
        'all': all_dep,
    },

    packages=find_packages(
        include=['bc_report', 'bc_pipelines.*'],
        exclude=[
            'contrib', 'docs', 'examples',
            '*.tests', '*.tests.*', 'tests.*', 'tests',
        ]
    ),
    package_data=package_data,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'bc_report = bc_report.cli:generate_report_cli',
        ],
    },

)
