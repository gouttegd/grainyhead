# grainyhead - Helper tools for GitHub
# Copyright © 2021,2023 Damien Goutte-Gattat
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
import time

from .util import parse_duration


class CachePolicy(object):
    """Represents the behaviour of a file cache."""

    def __init__(self, max_age):
        """Creates a new instance.

        If positive, the 'max_age' parameter is the number of seconds
        after which a cached file should be refreshed. This parameter
        can also accept some special values:
        - 0 indicates refresh should always occur, regardless of the age
          of the file;
        - -1 indicates the cache should be cleared;
        - -2 indicates the cache should be disabled.
        """

        self._now = time.time()
        self._max_age = max_age

    def refresh(self, age):
        """Indicates whether a refresh should occur.

        :param age: the modification time of the cached file, in seconds
            since the Unix epoch
        :return: True if the file should be refreshed, False otherwise
        """

        return self._now - age > self._max_age

    _refresh_policy = None
    _no_refresh_policy = None
    _reset_policy = None
    _disabled_policy = None
    _click_type = None

    @classmethod
    def from_string(cls, value):
        """Creates a new instance from a string representation."""

        value = value.lower()
        if value in ['disabled', 'no-cache']:
            return cls.DISABLED
        elif value in ['refresh', 'always']:
            return cls.REFRESH
        elif value in ['no-refresh', 'never']:
            return cls.NO_REFRESH
        elif value in ['reset', 'clear']:
            return cls.RESET
        elif (d := parse_duration(value, False)) is not None:
            return cls(d.total_seconds())
        else:
            return None

    @classmethod
    @property
    def REFRESH(cls):
        """A policy that cached data should always be refreshed."""

        if cls._refresh_policy is None:
            cls._refresh_policy = cls(max_age=0)
        return cls._refresh_policy

    @classmethod
    @property
    def NO_REFRESH(cls):
        """A policy that cached data should never be refreshed."""

        if cls._no_refresh_policy is None:
            cls._no_refresh_policy = cls(max_age=timedelta.max.total_seconds())
        return cls._no_refresh_policy

    @classmethod
    @property
    def RESET(cls):
        """A policy that cached data should be cleared and refreshed."""

        if cls._reset_policy is None:
            cls._reset_policy = cls(max_age=-1)
        return cls._reset_policy

    @classmethod
    @property
    def DISABLED(cls):
        """A policy that the cache should be completely disabled."""

        if cls._disabled_policy is None:
            cls._disabled_policy = cls(max_age=-2)
        return cls._disabled_policy

    @classmethod
    @property
    def ClickType(cls):
        if cls._click_type is None:
            from click import ParamType

            class CachePolicyParamType(ParamType):
                name = 'cache-policy'

                def convert(self, value, param, ctx):
                    if isinstance(value, cls):
                        return value

                    if p := cls.from_string(value):
                        return p
                    else:
                        self.fail(
                            f"Cannot convert '{value}' to a cache policy", param, ctx
                        )

            cls._click_type = CachePolicyParamType()

        return cls._click_type
