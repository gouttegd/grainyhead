# grainyhead - Helper tools for GitHub
# Copyright © 2021 Damien Goutte-Gattat
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
from fbcam.grainyhead import __version__

setup(
    name='grainyhead',
    version=__version__,
    description='Helper tools for GitHub',
    author='Damien Goutte-Gattat',
    author_email='dpg44@cam.ac.uk',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Licence :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.9'
        ],

    install_requires=[
        'click_shell >= 2.1',
        'ghapi'
        ],

    extras_require={
        'IPython': ['ipython']
        },

    packages=[
        'fbcam',
        'fbcam.grainyhead'
        ],

    entry_points={
        'console_scripts': [
            'grh = fbcam.grainyhead.main:grh'
            ]
        }
    )
