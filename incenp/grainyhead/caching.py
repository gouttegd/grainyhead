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

from datetime import datetime, timedelta
import json
import os.path
from os import makedirs
import time

from fastcore.xtras import dict2obj, obj2dict

from .providers import RepositoryProvider, RepositoryItemType, GITHUB_DATE_FORMAT
from .util import parse_duration


class CachePolicy(object):
    """Reresents the behaviour of a file cache."""

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


class FileRepositoryProvider(RepositoryProvider):
    """Provides access to cached data from a GitHub repository."""

    def __init__(self, directory, backend, policy):
        self._cachedir = directory
        self._backend = backend
        self._policy = policy

    def get_data(self, item_type, since=None):
        if self._policy == CachePolicy.DISABLED:
            return self._backend.get_data(item_type, since)

        data = []
        refresh = False

        data_file = self._get_data_file(item_type)
        if self._policy != CachePolicy.RESET and os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = dict2obj(json.load(f))
            mtime = os.path.getmtime(data_file)
            if self._policy.refresh(mtime):
                refresh = True
                since = self._get_last_item_date(item_type, data)

        if len(data) == 0:
            refresh = True
            since = None

        if refresh:
            new_data = self._backend.get_data(item_type, since)
            if since is not None:
                # Append existing data, if we asked for new data only
                new_data.extend(data)
            data = self._purge_duplicates(new_data, item_type)
            makedirs(self._cachedir, 0o755, True)
            with open(data_file, 'w') as f:
                json.dump(obj2dict(data), f, indent=0)

        return data

    def _get_data_file(self, item_type):
        filename = item_type.name.lower() + '.json'
        return os.path.join(self._cachedir, filename)

    def _get_last_item_date(self, item_type, data):
        if item_type == RepositoryItemType.ISSUES:
            # Force full refresh, so that we get updated status for
            # old issues
            return None
        elif item_type in [RepositoryItemType.LABELS, RepositoryItemType.TEAMS]:
            # Always fetch everything for those
            return None
        elif item_type == RepositoryItemType.COMMITTERS:
            # Always fetch everything for those
            return None
        elif item_type == RepositoryItemType.COMMITS:
            # Only get new commits
            return datetime.strptime(data[-1].commit.author.date, GITHUB_DATE_FORMAT)
        else:
            # Only get new other items
            return datetime.strptime(data[-1].created_at, GITHUB_DATE_FORMAT)

    def _purge_duplicates(self, data, item_type):
        # The data we get from GitHub sometimes contain duplicated items,
        # for unclear reasons. That can happen even we ask for the full
        # data in one single step. Here, we forcibly remove all duplicates.
        if item_type == RepositoryItemType.COMMITS:
            # Identify duplicates by SHA1 hash, then force descending
            # chronological order
            return sorted(
                {c.sha: c for c in data}.values(),
                reverse=True,
                key=lambda c: datetime.strptime(
                    c.commit.author.date, GITHUB_DATE_FORMAT
                ),
            )
        elif item_type == RepositoryItemType.LABELS:
            # Identify duplicates by label ID
            return list({l.id: l for l in data}.values())
        elif item_type == RepositoryItemType.TEAMS:
            # Identify duplicates by team "slugs"
            return list({t.slug: t for t in data}.values())
        elif item_type == RepositoryItemType.COMMITTERS:
            # Identify duplicates by login name
            return list({l.login: l for l in data}.values())
        else:
            # Identify duplicates by item ID, then force descending
            # chronological order
            return sorted(
                {i.id: i for i in data}.values(),
                reverse=True,
                key=lambda i: datetime.strptime(i.created_at, GITHUB_DATE_FORMAT),
            )
