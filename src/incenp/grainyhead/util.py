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

from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
import re

import click

_durations = {'d': 1, 'w': 7, 'm': 30, 'y': 365}
_periods = {'d': 'days', 'w': 'weeks', 'm': 'months', 'y': 'years'}
_date_formats = ['%Y-%m-%d', '%Y-%m']


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
        elif (delta := parse_duration(value)) is not None:
            return datetime.now(timezone.utc) - delta
        else:
            for fmt in _date_formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
            self.fail(f"Cannot convert '{value}' to a date", param, ctx)


class TimeIntervalParamType(click.ParamType):
    """A parameter type for Click representing a time interval.

    This parameter accepts:
    - Xd (or simply X), for an interval of X day(s);
    - Xw, for an interval of X week(s);
    - Xm, for an interval of X calendar month(s);
    - Xy, for an interval of X year(s);
    - 'weekly', as an alternative for '1w';
    - 'monthly', as an alternative for '1m';
    - 'quarterly', as an alternative for '3m';
    - 'yearly', as an alternative for '1y'.
    """

    name = 'interval'

    def convert(self, value, param, ctx):
        if isinstance(value, relativedelta):
            return value

        value = value.lower()
        if value == 'weekly':
            return relativedelta(weeks=1)
        elif value == 'monthly':
            return relativedelta(months=1)
        elif value == 'quarterly':
            return relativedelta(months=3)
        elif value == 'yearly':
            return relativedelta(years=1)
        elif (interval := parse_duration(value, True)) is not None:
            return interval
        else:
            self.fail(f"Cannot convert '{value}' to a time interval", param, ctx)


def parse_duration(value, relative=False):
    """Parse a string representing a duration.

    This function parses a string of the form 'Nf', where N is a
    positive number and f is a one-letter code representing a time unit:
    'd' for days, 'w' for weeks, 'm' for months, and 'y' for years. If f
    is omitted, 'd' is assumed.

    The returned value is a :class:`datetime.timedelta` object by
    default. If the 'relative' parameter is True, then the function
    returns a :class:`dateutil.relativedelta` object instead.

    In any case, if the provided value does not match the expected 'Nf'
    form, the function returns None.
    """

    if m := re.match('^([0-9]+)([dwmy])?$', value):
        n, f = m.groups()
        if not f:
            f = 'd'
        if relative:
            d = {_periods[f]: int(n)}
            return relativedelta(**d)
        else:
            return timedelta(days=int(n) * _durations[f])
    else:
        return None


Date = DateParamType()
Interval = TimeIntervalParamType()
