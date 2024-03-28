# grainyhead - Helper tools for GitHub
# Copyright © 2021,2022,2023,2024 Damien Goutte-Gattat
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

from datetime import datetime
from enum import Enum
import logging

from fastcore.basics import AttrDict
from fastcore.net import HTTP4xxClientError
from ghapi.page import date2gh

GITHUB_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'


def gh2date(dtstr):
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
    def creation_time(self):
        return datetime.strptime(self.created_at, GITHUB_DATE_FORMAT)

    @property
    def update_time(self):
        return datetime.strptime(self.updated_at, GITHUB_DATE_FORMAT)

    def _filter_time(self, time, after=None, before=None):
        return (not after or time > after) and (not before or time < before)

    def created(self, after=None, before=None):
        """Indicates whether the item was created in a given time span."""

        return self._filter_time(self.creation_time, after, before)

    def updated(self, after=None, before=None):
        """Indicates whether the item was updated in a given time span."""

        return self._filter_time(self.update_time, after, before)

    @property
    def user_name(self):
        """The name of the user who created this item."""

        return self.user.login

    @property
    def label_strings(self):
        """The labels associated with this item, if any."""

        return []

    def __hash__(self):
        return self.id


class IssueItem(RepositoryItem):
    """A GitHub issue.

    This can be either an actual "issue" or a "pull requests".
    """

    @property
    def close_time(self):
        if not self.closed_at:
            return None
        return datetime.strptime(self.closed_at, GITHUB_DATE_FORMAT)

    def closed(self, after=None, before=None):
        """Indicates whether the issue was closed in a given time span."""

        if not self.closed_at:
            return False
        return self._filter_time(self.close_time, after, before)

    @property
    def label_strings(self):
        return [l.name for l in self.labels]


class EventItem(RepositoryItem):
    """An event on an issue or a pull request."""

    @property
    def user_name(self):
        if self.actor is not None:
            return self.actor.login
        else:
            return None

    @property
    def label_strings(self):
        return [l.name for l in self.issue.labels]


class CommitItem(RepositoryItem):
    """A git commit."""

    @property
    def creation_time(self):
        return datetime.strptime(self.commit.author.date, GITHUB_DATE_FORMAT)

    @property
    def user_name(self):
        if self.author is not None:
            return self.author.login
        else:
            return self.commit.author.name

    def __hash__(self):
        return self.sha.__hash__()


class ReleaseItem(RepositoryItem):
    """A formal release."""

    @property
    def user_name(self):
        if self.author is not None:
            return self.author.login
        else:
            return None


class RepositoryProvider(object):
    """Provides access to the data from a GitHub repository."""

    def get_data(self, item_type, since=None):
        """Gets a specific type of data from the repository.

        :param item_type: the type of data to fetch
        :param since: only fetch data from after that timestamp
        :return: an array of AttrDict objects
        """

        pass

    @property
    def issues(self):
        return [
            i
            for i in self.get_data(RepositoryItemType.ISSUES)
            if not hasattr(i, 'pull_request')
        ]

    @property
    def pull_requests(self):
        return [
            i
            for i in self.get_data(RepositoryItemType.ISSUES)
            if hasattr(i, 'pull_request')
        ]

    @property
    def comments(self):
        return self.get_data(RepositoryItemType.COMMENTS)

    @property
    def teams(self):
        return self.get_data(RepositoryItemType.TEAMS)

    @property
    def labels(self):
        return self.get_data(RepositoryItemType.LABELS)

    @property
    def events(self):
        return self.get_data(RepositoryItemType.EVENTS)

    @property
    def commits(self):
        return self.get_data(RepositoryItemType.COMMITS)

    @property
    def releases(self):
        return self.get_data(RepositoryItemType.RELEASES)

    @property
    def committers(self):
        return self.get_data(RepositoryItemType.COMMITTERS)


class OnlineRepositoryProvider(RepositoryProvider):
    """Provides direct access to the data from a GitHub repository."""

    def __init__(self, api):
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

    def get_data(self, item_type, since=None):
        data = None
        if item_type == RepositoryItemType.ISSUES:
            data = self._fetch(
                self._api.issues.list_for_repo, apiargs={'state': 'all'}, since=since
            )
        elif item_type == RepositoryItemType.TEAMS:
            data = self._fetch_teams()
        elif item_type == RepositoryItemType.COMMITTERS:
            data = self._fetch_committers()
        else:
            data = self._fetch(self._calls[item_type], since=since)
        return data

    def _fetch_committers(self):
        committers = self._api.repos.list_contributors(per_page=100)
        last_page = self._api.last_page()
        page = 0

        while page < last_page:
            page += 1
            committers.extend(
                self._api.repos.list_contributors(per_page=100, page=page)
            )

        return committers

    def _fetch(self, apicall, apiargs={}, since=None):
        """Generic method to fetch data from GitHub."""

        if since is not None:
            if apicall in self._calls_without_since:
                # No support for 'since=' parameter in those calls,
                # we need to ensure manually that we don't get more
                # than what we want
                return self._fetch_since(apicall, since, apiargs)
            apiargs['since'] = date2gh(since)

        things = apicall(per_page=100, **apiargs)
        last_page = self._api.last_page()
        page = 0

        while page < last_page:
            page += 1
            things.extend(apicall(per_page=100, page=page, **apiargs))

        return things

    def _fetch_since(self, apicall, since, apiargs={}):
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

    def _fetch_teams(self):
        teams = [AttrDict({'slug': '__collaborators'})]
        try:
            teams.extend(self._fetch(self._api.teams.list))
        except HTTP4xxClientError:
            logging.warn(
                "Cannot get teams list (possibly due to " "insufficient access rights)"
            )

        for team in teams:
            team['members'] = self._fetch_team_members(team.slug)

        return teams

    def _fetch_team_members(self, slug):
        members = []
        try:
            if slug == '__collaborators':
                members = self._fetch(self._api.repos.list_collaborators)
            else:
                members = self._fetch(
                    self._api.teams.list_members_in_org, {'team_slug': slug}
                )
        except HTTP4xxClientError:
            logging.warn(
                "Cannot get team members (possibly due to "
                "insufficient access rights)"
            )

        return members


class MemoryRepositoryProvider(RepositoryProvider):
    """In-memory cache for data from a GitHub repository."""

    _wrappers = {
        RepositoryItemType.ISSUES: IssueItem,
        RepositoryItemType.COMMITS: CommitItem,
        RepositoryItemType.COMMENTS: RepositoryItem,
        RepositoryItemType.EVENTS: EventItem,
        RepositoryItemType.RELEASES: ReleaseItem,
    }

    def __init__(self, backend):
        """Creates a new instance.

        :param backend: a RepositoryProvider object from which to fetch
            the data that are not already in memory
        """

        self._backend = backend
        self._data = {}

    def get_data(self, item_type, since=None):
        if item_type not in self._data:
            items = self._backend.get_data(item_type, since)
            wrapper = self._wrappers.get(item_type, None)
            if wrapper is not None:
                for item in items:
                    item.__class__ = wrapper
            self._data[item_type] = items
        return self._data[item_type]
