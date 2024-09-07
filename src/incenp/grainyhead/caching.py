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
import os.path
import time
import re

_durations = {'d': 1, 'w': 7, 'm': 30, 'y': 365}


class CachePolicy(object):
    """Represents the behaviour of a file cache.

    Once a CachePolicy object has been created (typically using the
    static constructor from_string, or one of the static properties for
    special policies), use the refresh_file() method to determine if a
    given file should be refreshed:

    if my_policy.refresh(my_cache_file):
        # refresh the cache file
    else:
        # no need for refresh

    Use the refresh() method to check an arbitrary timestamp against the
    policy (e.g. if the cached data is not in a file):

    if my_policy.refresh(timestamp_of_last_refresh):
        # refresh the data
    """

    def __init__(self, max_age):
        """Creates a new instance.

        If positive, the 'max_age' parameter is the number of seconds
        after which a cached file should be refreshed. This parameter
        can also accept some special values:
        - 0 indicates refresh should always occur, regardless of the age
          of the file;
        - -1 indicates the cache should be cleared;
        - -2 indicates the cache should be disabled.

        It is recommended to obtain such special policies using the
        static properties REFRESH, RESET, and DISABLED, rather than
        calling this constructor. This allows comparing a policy
        against those pre-established policies as follows:

        if my_policy == CachePolicy.RESET:
            # force reset

        rather than calling my_policy.is_reset().
        """

        self._now = time.time()
        self._max_age = max_age

    def refresh(self, then):
        """Indicates whether a refresh should occur for data last refreshed
        at the indicated time.

        :param then: the time the data were last cached or refreshed, in
            seconds since the Unix epoch
        :return: True if the data should be refreshed, False otherwise
        """

        return self._now - then > self._max_age

    def refresh_file(self, pathname):
        """Indicates whether the specified file should be refreshed.

        This uses the last modification time of the file to determine the
        "age" of the cached data.

        :param pathname: the path to the file that maybe should be refreshed.
        :return: True if the file should be refreshed, False otherwise.
        """

        return self.refresh(os.path.getmtime())

    def is_always_refresh(self):
        """Indicates whether this policy mandates a systematic refresh
        of the cache."""

        return self._max_age == 0

    def is_never_refresh(self):
        """Indicates whether this policy mandates never refreshing the cache."""

        return self._max_age == timedelta.max.total_seconds()

    def is_reset(self):
        """Indicates whether this policy mandates a reset of the cache."""

        return self._max_age == -1

    def is_disabled(self):
        """Indicates whether this policy mandates disabling the cache."""

        return self._max_age == -2

    _refresh_policy = None
    _no_refresh_policy = None
    _reset_policy = None
    _disabled_policy = None
    _click_type = None

    @classmethod
    def from_string(cls, value):
        """Creates a new instance from a string representation.

        The value can be either:
        - a number of seconds, followed by 's' (e.g. '3600s');
        - a number of days, optionally followed by 'd' (e.g. '5d');
        - a number of weeks, followed by 'w' (e.g. '2w');
        - a number of months, followed by 'm' (e.g. '3m');
        - a number of years, followed by 'y' (e.g. '2y');

        Such a value will result in a policy where cached files are
        refreshed after the elapsed number of seconds, days, weeks,
        months, or years. Note that in this context, a 'month' is
        always 30 days and a 'year' is always 365 days. That is, '3m' is
        merely a shortcut for '90d' (or simply '90') and '2y' is merely
        a shortcut for '730d'.

        The value can also be:
        - 'disabled' or 'no-cache', to get the DISABLED policy;
        - 'refresh' or 'always', to get the REFRESH policy;
        - 'no-refresh' or 'never', to get the NO_REFRESH policy'
        - 'reset' or 'clear, to get the RESET policy.

        Any other value will cause None to be returned.
        """

        value = value.lower()
        if value in ['disabled', 'no-cache']:
            return cls.DISABLED
        elif value in ['refresh', 'always']:
            return cls.REFRESH
        elif value in ['no-refresh', 'never']:
            return cls.NO_REFRESH
        elif value in ['reset', 'clear']:
            return cls.RESET
        else:
            if m := re.match('^([0-9]+)([sdwmy])?', value):
                n, f = m.groups()
                if not f:
                    f = 'd'
                if f == 's':
                    return cls(int(n))
                else:
                    return cls(timedelta(days=int(n) * _durations[f]).total_seconds())
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
        """Helper class to parse a CachingPolicy with Click.

        Use that class as the 'type' of a Click option to let Click
        automatically convert the value of the option into a
        CachingPolicy instance.

        Ex:

        @click.option('--caching', type=CachePolicy.ClickType,
                      default=CachePolicy.DISABLED)
        """

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
