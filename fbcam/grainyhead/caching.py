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

from datetime import datetime, timedelta
import json
import os.path
from os import makedirs
import time

from fastcore.xtras import dict2obj, obj2dict

from .providers import (RepositoryProvider, RepositoryItemType,
                        GITHUB_DATE_FORMAT)


class FileRepositoryProvider(RepositoryProvider):
    """Provides access to cached data from a GitHub repository."""

    def __init__(self, directory, backend):
        self._cachedir = directory
        self._backend = backend
        self._stale_cutoff = timedelta(days=30)

    def get_data(self, item_type, since=None):
        data = []
        now = time.time()
        refresh = False

        data_file = self._get_data_file(item_type)
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = dict2obj(json.load(f))
            mtime = os.path.getmtime(data_file)
            if now - self._stale_cutoff.total_seconds() > mtime:
                refresh = True
                since = self._get_last_item_date(item_type, data)

        if len(data) == 0:
            refresh = True
            since = None

        if refresh:
            data.extend(self._backend.get_data(item_type, since))
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
        elif item_type == RepositoryItemType.COMMITS:
            # Only get new commits
            return datetime.strptime(data[-1].commit.author.date,
                                     GITHUB_DATE_FORMAT)
        else:
            # Only get new other items
            return datetime.strptime(data[-1].created_at, GITHUB_DATE_FORMAT)
