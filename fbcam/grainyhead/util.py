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

from datetime import timedelta
import re

_durations = { 'd': 1, 'w': 7, 'm': 30, 'y': 365 }


def parse_duration(spec):
    m = re.match('([0-9]+)([dwmy])?', spec)
    if not m:
        raise RuntimeError(f"Invalid duration: {spec}")

    n, f = m.groups()
    if not f:
        f = 'd'
    return timedelta(days = int(n) * _durations[f])
