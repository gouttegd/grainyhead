# grainyhead - Helper tools for GitHub
# Copyright © 2021,2022,2023,2025 Damien Goutte-Gattat
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

from typing import Optional

from fastcore.basics import AttrDict  # type: ignore
from ghapi.core import GhApi  # type: ignore

from .providers import IssueItem, MemoryRepositoryProvider, RepositoryProvider


class Repository(object):
    _labels: Optional[list[str]]
    _teams: Optional[dict[str, AttrDict]]
    _committers: Optional[list[str]]
    _commenters: Optional[list[str]]

    def __init__(self, api: GhApi, backend: RepositoryProvider):
        self._api = api
        self._provider = MemoryRepositoryProvider(backend)

        self._labels = None
        self._teams = None
        self._committers = None
        self._commenters = None

    @property
    def issues(self) -> list[IssueItem]:
        return [i for i in self._provider.issues if i.closed_at is None]

    @property
    def all_issues(self) -> list[IssueItem]:
        return self._provider.issues

    @property
    def pull_requests(self) -> list[IssueItem]:
        return [i for i in self._provider.pull_requests if i.closed_at is None]

    @property
    def all_pull_requests(self) -> list[IssueItem]:
        return self._provider.pull_requests

    @property
    def comments(self):
        return self._provider.comments

    @property
    def events(self):
        return self._provider.events

    @property
    def commits(self):
        return self._provider.commits

    @property
    def releases(self):
        return self._provider.releases

    @property
    def labels(self) -> list[str]:
        if self._labels is None:
            self._labels = [l.name for l in self._provider.labels]
        return self._labels

    @property
    def contributors(self) -> list[str]:
        return list(set(self.committers + self.commenters))

    @property
    def committers(self) -> list[str]:
        if self._committers is None:
            self._committers = [
                l.login
                for l in self._provider.committers
                if not l.login.endswith("[bot]")
            ]
        return self._committers

    @property
    def commenters(self) -> list[str]:
        if self._commenters is None:
            commenters = [
                i.user.login
                for i in self.all_issues
                if not i.user.login.endswith("[bot]")
            ]
            commenters.extend(
                [
                    c.user.login
                    for c in self.comments
                    if not c.user.login.endswith("[bot]")
                ]
            )
            self._commenters = list(set(commenters))
        return self._commenters

    @property
    def collaborators(self) -> list[str]:
        return [m.login for m in self.get_team()]

    def get_team(self, name: str = "__collaborators") -> list[AttrDict]:
        if self._teams is None:
            self._teams = {}
            for team in self._provider.teams:
                self._teams[team.slug] = team
        return self._teams[name].members

    def get_usernames(self, group: str = "__collaborators") -> list[str]:
        if group == "__contributors":
            return self.contributors
        elif group == "__committers":
            return self.committers
        elif group == "__commenters":
            return self.commenters
        else:
            return [u.login for u in self.get_team(group)]

    def create_label(self, name: str, color: str, description: str) -> None:
        if name not in self.labels:
            self._api.issues.create_label(name, color, description)
            self.labels.append(name)

    def close_issue(
        self,
        issue: IssueItem,
        label: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        if label:
            self._api.issues.add_labels(issue.number, [label])
        if comment:
            self._api.issues.create_comment(issue.number, comment)
        self._api.issues.update(issue.number, state="closed")
