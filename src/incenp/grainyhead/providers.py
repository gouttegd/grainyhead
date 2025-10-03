# grainyhead - Helper tools for GitHub
# Copyright © 2021,2022,2023,2024,2025 Damien Goutte-Gattat
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

import json
import logging
import os.path
from datetime import datetime
from enum import Enum
from os import makedirs
from typing import Any, Callable, Optional

from fastcore.basics import AttrDict  # type: ignore
from fastcore.net import HTTP4xxClientError  # type: ignore
from fastcore.xtras import dict2obj, obj2dict  # type: ignore
from ghapi.core import GhApi  # type: ignore
from ghapi.page import date2gh  # type: ignore

from .caching import CachePolicy

GITHUB_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def gh2date(dtstr: str) -> datetime:
    return datetime.strptime(dtstr, GITHUB_DATE_FORMAT)


class RepositoryItemType(Enum):
    """The types of items we are dealing with from GitHub."""

    ISSUES = 1
    COMMENTS = 2
    TEAMS = 3
    LABELS = 4
    EVENTS = 5
    COMMITS = 6
    RELEASES = 7
    COMMITTERS = 8


class RepositoryItem(AttrDict):
    """An item from a GitHub repository.

    This class extends the AttrDict class used by GhApi to provide
    helper methods to manipulate the items.
    """

    @property
    def creation_time(self) -> datetime:
        return datetime.strptime(self.created_at, GITHUB_DATE_FORMAT)

    @property
    def update_time(self) -> datetime:
        return datetime.strptime(self.updated_at, GITHUB_DATE_FORMAT)

    def _filter_time(
        self,
        time: datetime,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None,
    ) -> bool:
        return (not after or time > after) and (not before or time < before)

    def created(
        self, after: Optional[datetime] = None, before: Optional[datetime] = None
    ) -> bool:
        """Indicates whether the item was created in a given time span."""

        return self._filter_time(self.creation_time, after, before)

    def updated(
        self, after: Optional[datetime] = None, before: Optional[datetime] = None
    ) -> bool:
        """Indicates whether the item was updated in a given time span."""

        return self._filter_time(self.update_time, after, before)

    @property
    def user_name(self) -> Optional[str]:
        """The name of the user who created this item."""

        return self.user.login

    @property
    def label_strings(self) -> list[str]:
        """The labels associated with this item, if any."""

        return []

    def __hash__(self) -> int:
        return self.id


class IssueItem(RepositoryItem):
    """A GitHub issue.

    This can be either an actual "issue" or a "pull requests".
    """

    @property
    def close_time(self) -> Optional[datetime]:
        if not self.closed_at:
            return None
        return datetime.strptime(self.closed_at, GITHUB_DATE_FORMAT)

    def closed(
        self, after: Optional[datetime] = None, before: Optional[datetime] = None
    ) -> bool:
        """Indicates whether the issue was closed in a given time span."""

        if not self.closed_at:
            return False
        return self._filter_time(
            datetime.strptime(self.close_at, GITHUB_DATE_FORMAT), after, before
        )

    @property
    def label_strings(self) -> list[str]:
        return [l.name for l in self.labels]


class EventItem(RepositoryItem):
    """An event on an issue or a pull request."""

    @property
    def user_name(self) -> Optional[str]:
        if self.actor is not None:
            return self.actor.login
        else:
            return None

    @property
    def label_strings(self) -> list[str]:
        return [l.name for l in self.issue.labels]


class CommitItem(RepositoryItem):
    """A git commit."""

    @property
    def creation_time(self) -> datetime:
        return datetime.strptime(self.commit.author.date, GITHUB_DATE_FORMAT)

    @property
    def user_name(self) -> str:
        if self.author is not None:
            return self.author.login
        else:
            return self.commit.author.name

    def __hash__(self) -> int:
        return self.sha.__hash__()


class ReleaseItem(RepositoryItem):
    """A formal release."""

    @property
    def user_name(self) -> Optional[str]:
        if self.author is not None:
            return self.author.login
        else:
            return None


class RepositoryProvider(object):
    """Provides access to the data from a GitHub repository."""

    def get_data(
        self, item_type: RepositoryItemType, since: Optional[datetime] = None
    ) -> Any:
        """Gets a specific type of data from the repository.

        :param item_type: the type of data to fetch
        :param since: only fetch data from after that timestamp
        :return: an array of AttrDict objects
        """

        pass

    @property
    def issues(self) -> list[IssueItem]:
        return [
            i
            for i in self.get_data(RepositoryItemType.ISSUES)
            if not hasattr(i, "pull_request")
        ]

    @property
    def pull_requests(self) -> list[IssueItem]:
        return [
            i
            for i in self.get_data(RepositoryItemType.ISSUES)
            if hasattr(i, "pull_request")
        ]

    @property
    def comments(self) -> list[AttrDict]:
        return self.get_data(RepositoryItemType.COMMENTS)

    @property
    def teams(self) -> list[AttrDict]:
        return self.get_data(RepositoryItemType.TEAMS)

    @property
    def labels(self) -> list[AttrDict]:
        return self.get_data(RepositoryItemType.LABELS)

    @property
    def events(self) -> list[EventItem]:
        return self.get_data(RepositoryItemType.EVENTS)

    @property
    def commits(self) -> list[CommitItem]:
        return self.get_data(RepositoryItemType.COMMITS)

    @property
    def releases(self) -> list[ReleaseItem]:
        return self.get_data(RepositoryItemType.RELEASES)

    @property
    def committers(self) -> list[AttrDict]:
        return self.get_data(RepositoryItemType.COMMITTERS)


class OnlineRepositoryProvider(RepositoryProvider):
    """Provides direct access to the data from a GitHub repository."""

    def __init__(self, api: GhApi):
        """Creates a new instance.

        :param api: a ghapi.core.GhApi object
        """

        self._api = api
        self._calls = {
            RepositoryItemType.COMMENTS: api.issues.list_comments_for_repo,
            RepositoryItemType.LABELS: api.issues.list_labels_for_repo,
            RepositoryItemType.EVENTS: api.issues.list_events_for_repo,
            RepositoryItemType.COMMITS: api.repos.list_commits,
            RepositoryItemType.RELEASES: api.repos.list_releases,
        }
        self._calls_without_since = [
            api.issues.list_events_for_repo,
            api.repos.list_releases,
        ]

    def get_data(
        self, item_type: RepositoryItemType, since: Optional[datetime] = None
    ) -> Any:
        data = None
        if item_type == RepositoryItemType.ISSUES:
            data = self._fetch(
                self._api.issues.list_for_repo, apiargs={"state": "all"}, since=since
            )
        elif item_type == RepositoryItemType.TEAMS:
            data = self._fetch_teams()
        elif item_type == RepositoryItemType.COMMITTERS:
            data = self._fetch_committers()
        else:
            data = self._fetch(self._calls[item_type], since=since)
        return data

    def _fetch_committers(self) -> list[AttrDict]:
        committers = self._api.repos.list_contributors(per_page=100)
        last_page = self._api.last_page()
        page = 0

        while page < last_page:
            page += 1
            committers.extend(
                self._api.repos.list_contributors(per_page=100, page=page)
            )

        return committers

    def _fetch(
        self, apicall: Callable, apiargs: dict = {}, since: Optional[datetime] = None
    ) -> list[AttrDict]:
        """Generic method to fetch data from GitHub."""

        if since is not None:
            if apicall in self._calls_without_since:
                # No support for 'since=' parameter in those calls,
                # we need to ensure manually that we don't get more
                # than what we want
                return self._fetch_since(apicall, since, apiargs)
            apiargs["since"] = date2gh(since)

        things = apicall(per_page=100, **apiargs)
        last_page = self._api.last_page()
        page = 0

        while page < last_page:
            page += 1
            things.extend(apicall(per_page=100, page=page, **apiargs))

        return things

    def _fetch_since(
        self, apicall: Callable, since: datetime, apiargs: dict = {}
    ) -> list[AttrDict]:
        """Specialized method for items without 'since=' support."""

        things = apicall(per_page=100, **apiargs)
        last_page = self._api.last_page()
        page = 0

        loop = True
        while loop and page < last_page:
            if gh2date(things[-1].created_at) <= since:
                # Stop fetching if we got what we were looking for
                loop = False
            else:
                page += 1
                things.extend(apicall(per_page=100, page=page, **apiargs))

        # Remove everything before the cutoff timestamp
        return [i for i in things if gh2date(i.created_at) >= since]

    def _fetch_teams(self) -> list[AttrDict]:
        teams = [AttrDict({"slug": "__collaborators"})]
        try:
            teams.extend(self._fetch(self._api.teams.list))
        except HTTP4xxClientError:
            logging.warn(
                "Cannot get teams list (possibly due to insufficient access rights)"
            )

        for team in teams:
            team["members"] = self._fetch_team_members(team.slug)

        return teams

    def _fetch_team_members(self, slug: str) -> list[AttrDict]:
        members = []
        try:
            if slug == "__collaborators":
                members = self._fetch(self._api.repos.list_collaborators)
            else:
                members = self._fetch(
                    self._api.teams.list_members_in_org, {"team_slug": slug}
                )
        except HTTP4xxClientError:
            logging.warn(
                "Cannot get team members (possibly due to insufficient access rights)"
            )

        return members


class FileRepositoryProvider(RepositoryProvider):
    """Provides access to cached data from a GitHub repository."""

    def __init__(
        self, directory: str, backend: RepositoryProvider, policy: CachePolicy
    ):
        self._cachedir = directory
        self._backend = backend
        self._policy = policy

    def get_data(
        self, item_type: RepositoryItemType, since: Optional[datetime] = None
    ) -> list[AttrDict]:
        if self._policy == CachePolicy.DISABLED:
            return self._backend.get_data(item_type, since)

        data = []
        refresh = False

        data_file = self._get_data_file(item_type)
        if self._policy != CachePolicy.RESET and os.path.exists(data_file):
            with open(data_file, "r") as f:
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
            with open(data_file, "w") as f:
                json.dump(obj2dict(data), f, indent=0)

        return data

    def _get_data_file(self, item_type: RepositoryItemType) -> str:
        filename = item_type.name.lower() + ".json"
        return os.path.join(self._cachedir, filename)

    def _get_last_item_date(
        self, item_type: RepositoryItemType, data: list[AttrDict]
    ) -> Optional[datetime]:
        if item_type == RepositoryItemType.ISSUES:
            # Force full refresh, so that we get updated status for
            # old issues
            return None
        elif item_type in [
            RepositoryItemType.LABELS,
            RepositoryItemType.TEAMS,
            RepositoryItemType.COMMITTERS,
        ]:
            # Always fetch everything for those
            return None
        elif item_type == RepositoryItemType.COMMITS:
            # Only get new commits
            return datetime.strptime(data[-1].commit.author.date, GITHUB_DATE_FORMAT)
        else:
            # Only get new other items
            return datetime.strptime(data[-1].created_at, GITHUB_DATE_FORMAT)

    def _purge_duplicates(
        self, data: list[AttrDict], item_type: RepositoryItemType
    ) -> list[AttrDict]:
        # The data we get from GitHub sometimes contain duplicated items,
        # for unclear reasons. That can happen even when we ask for the
        # full data in one single step. Here, we forcibly remove all
        # duplicates
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


class MemoryRepositoryProvider(RepositoryProvider):
    """In-memory cache for data from a GitHub repository."""

    _wrappers = {
        RepositoryItemType.ISSUES: IssueItem,
        RepositoryItemType.COMMITS: CommitItem,
        RepositoryItemType.COMMENTS: RepositoryItem,
        RepositoryItemType.EVENTS: EventItem,
        RepositoryItemType.RELEASES: ReleaseItem,
    }

    def __init__(self, backend: RepositoryProvider):
        """Creates a new instance.

        :param backend: a RepositoryProvider object from which to fetch
            the data that are not already in memory
        """

        self._backend = backend
        self._data: dict[RepositoryItemType, list[Any]] = {}

    def get_data(
        self, item_type: RepositoryItemType, since: Optional[datetime] = None
    ) -> list[Any]:
        if item_type not in self._data:
            items = self._backend.get_data(item_type, since)
            wrapper = self._wrappers.get(item_type, None)
            if wrapper is not None:
                for item in items:
                    item.__class__ = wrapper
            self._data[item_type] = items
        return self._data[item_type]
