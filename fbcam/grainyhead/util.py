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

from datetime import datetime, timedelta, timezone
import re

import click

_durations = { 'd': 1, 'w': 7, 'm': 30, 'y': 365 }
_date_formats = [
    '%Y-%m-%d',
    '%Y-%m'
    ]


class DateParamType(click.ParamType):
    """A parameter type for Click representing a date.

    This differs from the standard click.DateTime in that it also allows
    to specify a date as a number of days, weeks, months, or years from
    the current date. It also recognizes some special values.

    Specifically, this parameter accepts:
    - a plain date, written as YYYY-MM-DD or YYYY-MM;
    - Xd (or simply X), for the date X day(s) ago;
    - Xw, for the date X week(s) ago;
    - Xm, for the date X month(s) ago;
    - Xy, for the date Y year(s) ago;
    - 'now', for the current date;
    - 'origin', for the earliest possible date.
    """

    name = 'date'

    def convert(self, value, param, ctx):
        if isinstance(value, datetime):
            return value

        if value.lower() == 'now':
            return datetime.now(timezone.utc)
        elif value.lower() == 'origin':
            return datetime.min.replace(tzinfo=timezone.utc)
        elif m := re.match('^([0-9]+)([dwmy])?$', value):
            n, f = m.groups()
            if not f:
                f = 'd'
            now = datetime.now(timezone.utc)
            delta = timedelta(days=int(n) * _durations[f])
            return now - delta
        else:
            for fmt in _date_formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            self.fail(f"Cannot convert '{value}' to a date", param, ctx)


Date = DateParamType()
