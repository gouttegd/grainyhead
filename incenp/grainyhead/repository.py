# grainyhead - Helper tools for GitHub
# Copyright © 2021,2022 Damien Goutte-Gattat
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

from .providers import MemoryRepositoryProvider


class Repository(object):

    def __init__(self, api, backend):
        self._api = api
        self._provider = MemoryRepositoryProvider(backend)
        self._labels = None
        self._teams = None

    @property
    def issues(self):
        return [i for i in self._provider.issues if i.closed_at is None]

    @property
    def all_issues(self):
        return self._provider.issues

    @property
    def pull_requests(self):
        return [i for i in self._provider.pull_requests if i.closed_at is None]

    @property
    def all_pull_requests(self):
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
    def labels(self):
        if self._labels is None:
            self._labels = [l.name for l in self._provider.labels]
        return self._labels

    @property
    def contributors(self):
        return [m.login for m in self.get_team()]

    def get_team(self, name='__collaborators'):
        if self._teams is None:
            self._teams = {}
            for team in self._provider.teams:
                self._teams[team.slug] = team
        return self._teams[name].members

    def create_label(self, name, color, description):
        if not name in self.labels:
            self._api.issues.create_label(name, color, description)
            self._labels.append(name)

    def close_issue(self, issue, label=None, comment=None):
        if label:
            self._api.issues.add_labels(issue.number, [label])
        if comment:
            self._api.issues.create_comment(issue.number, comment)
        self._api.issues.update(issue.number, state='closed')
