# grainyhead - Helper tools for GitHub
# Copyright © 2021,2022,2023 Damien Goutte-Gattat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup
from incenp.grainyhead import __version__

with open('README.md', 'r') as fh:
    long_description = fh.read()

with open('requirements.txt', 'r') as fh:
    requirements = fh.readlines()

setup(
    name='grainyhead',
    version=__version__,
    description='Helper tools for GitHub',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Damien Goutte-Gattat',
    author_email='dpg44@cam.ac.uk',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.9',
        'Intended Audience :: Developers',
    ],
    install_requires=[line.strip() for line in requirements],
    extras_require={'IPython': ['ipython']},
    packages=['incenp', 'incenp.grainyhead'],
    entry_points={'console_scripts': ['grainyhead = incenp.grainyhead.main:grh']},
    command_options={
        'build_sphinx': {
            'project': ('setup.py', 'GrainyHead'),
            'version': ('setup.py', __version__),
            'release': ('setup.py', __version__),
        }
    },
)
