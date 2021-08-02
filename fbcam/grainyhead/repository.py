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

from datetime import datetime

from ghapi.core import GhApi
from ghapi.page import pages
from fastcore.basics import AttrDict


class Repository(object):

    def __init__(self, owner, name, token=None):
        self._owner = owner
        self._api = GhApi(owner=owner, repo=name, token=token)
        self._issues = None
        self._teams = {}
        self._labels = None

    def get_issues(self):
        if not self._issues:
            self._fetch_issues()

        return [i for i in self._issues if not hasattr(i, 'pull_request')]

    def get_pull_requests(self):
        if not self._issues:
            self._fetch_issues()

        return [i for i in self._issues if hasattr(i, 'pull_request')]

    def get_team(self, name='__collaborators'):
        if name not in self._teams:
            if name == '__collaborators':
                self._fetch_collaborators()
            else:
                self._fetch_team(name)

        return self._teams[name]

    def get_labels(self):
        if not self._labels:
            self._fetch_labels()
        return self._labels

    def create_label(self, name, color, description):
        if not name in self.get_labels():
            self._api.issues.create_label(name, color, description)
            self.get_labels().append(name)

    def _fetch_issues(self):
        self._issues = self._api.issues.list_for_repo(per_page=100)
        last_page = self._api.last_page()
        if last_page > 0:
            self._issues = pages(self._api.issues.list_for_repo,
                                 last_page).concat()

        for issue in self._issues:
            issue.__class__ = Issue
            issue._api = self._api

    def _fetch_team(self, name):
        team = self._api.teams.list_members_in_org(org=self._owner,
                                                   team_slug=name,
                                                   per_page=100)
        last_page = self._api.last_page()
        if last_page > 0:
            team = pages(self._api.teams.list_members_in_org,
                         last_page).concat()

        self._teams[name] = team

    def _fetch_collaborators(self):
        collabs = self._api.repos.list_collaborators(per_page=100)
        last_page = self._api.last_page()
        if last_page > 0:
            collabs = pages(self._api.repos.list_collaborators,
                            last_page).concat()
        self._teams['__collaborators'] = collabs

    def _fetch_labels(self):
        labels = self._api.issues.list_labels_for_repo(per_page=100)
        last_page = self._api.last_page()
        if last_page > 0:
            labels = pages(self._api.issues.list_labels_for_repo,
                           last_page).concat()

        self._labels = [l.name for l in labels]


class Issue(AttrDict):

    def is_older_than(self, cutoff):
        update = datetime.strptime(self.updated_at, '%Y-%m-%dT%H:%M:%S%z')
        return update < cutoff

    def close(self, label=None, comment=None):
        if label:
            self._api.issues.add_labels(self.number, [label])
        if comment:
            self._api.issues.create_comment(self.number, comment)
        self._api.issues.update(self.number, state='closed')
