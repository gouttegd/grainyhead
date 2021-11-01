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

_GITHUB_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'


class Repository(object):

    def __init__(self, owner, name, token=None):
        self._owner = owner
        self._api = GhApi(owner=owner, repo=name, token=token)
        self._issues = None
        self._comments = None
        self._teams = {}
        self._labels = None
        self._events = None
        self._commits = None
        self._releases = None

    @property
    def issues_pulls(self):
        if not self._issues:
            self._issues = self._fetch(self._api.issues.list_for_repo,
                                       apiargs={'state': 'all'},
                                       wrapper=Issue)
            Issue._api = self._api

        return self._issues

    @property
    def issues(self):
        return [i for i in self.issues_pulls if not hasattr(i, 'pull_request')
                and i.closed_at is None]

    @property
    def all_issues(self):
        return [i for i in self.issues_pulls if not hasattr(i, 'pull_request')]

    @property
    def pull_requests(self):
        return [i for i in self.issues_pulls if hasattr(i, 'pull_request')
                and i.closed_at is None]

    @property
    def all_pull_requests(self):
        return [i for i in self.issues_pulls if hasattr(i, 'pull_request')]

    @property
    def comments(self):
        if not self._comments:
            self._comments = self._fetch(self._api.issues.list_comments_for_repo,
                                         wrapper=GithubObject)

        return self._comments

    @property
    def events(self):
        if not self._events:
            self._events = self._fetch(self._api.issues.list_events_for_repo,
                                       wrapper=GithubObject)

        return self._events

    @property
    def commits(self):
        if not self._commits:
            self._commits = self._fetch(self._api.repos.list_commits,
                                        wrapper=Commit)

        return self._commits

    @property
    def releases(self):
        if not self._releases:
            self._releases = self._fetch(self._api.repos.list_releases,
                                         wrapper=GithubObject)

        return self._releases

    @property
    def labels(self):
        if not self._labels:
            labels = self._fetch(self._api.issues.list_labels_for_repo)
            self._labels = [l.name for l in labels]

        return self._labels

    def get_team(self, name='__collaborators'):
        if name not in self._teams:
            if name == '__collaborators':
                team = self._fetch(self._api.repos.list_collaborators)
            else:
                team = self._fetch(self._api.teams.list_members_in_org,
                                   apiargs={'org': self._owner,
                                            'team_slug': name})
            self._teams[name] = team

        return self._teams[name]

    def create_label(self, name, color, description):
        if not name in self.labels:
            self._api.issues.create_label(name, color, description)
            self.labels.append(name)

    def get_metrics(self, start, end, team='__collaborators'):
        m = {}
        members = [m.login for m in self.get_team(team)]

        issues_opened = [i for i in self.all_issues
                         if i.created(after=start, before=end)]
        m['Issues opened'] = (len(issues_opened),
                              len([i for i in issues_opened
                                   if i.user.login in members]))

        issues_closes = [e for e in self.events
                         if e.event == 'closed'
                         and e.created(after=start, before=end)
                         and not hasattr(e.issue, 'pull_request')]
        m['Issues closed'] = (len(issues_closes),
                              len([e for e in issues_closes
                                   if e.actor.login in members]))

        pulls_opened = [p for p in self.all_pull_requests
                        if p.created(after=start, before=end)]
        m['Pull requests opened'] = (len(pulls_opened),
                                     len([p for p in pulls_opened
                                          if p.user.login in members]))

        pulls_closes = [e for e in self.events
                        if e.event == 'closed'
                        and e.created(after=start, before=end)
                        and hasattr(e.issue, 'pull_request')]
        m['Pull requests closed'] = (len(pulls_closes),
                                     len([e for e in pulls_closes
                                          if e.actor.login in members]))

        merges = [e for e in self.events if e.event == 'merged'
                  and e.created(after=start, before=end)]
        m['Pull requests merged'] = (len(merges),
                                     len([e for e in merges
                                          if e.actor.login in members]))

        comments = [c for c in self.comments
                    if c.created(after=start, before=end)]
        m['Comments'] = (len(comments),
                         len([c for c in comments
                              if c.user.login in members]))

        commits = [c for c in self.commits
                   if c.created(after=start, before=end)]
        m['Commits'] = (len(commits),
                        len([c for c in commits
                             if c.author and c.author.login in members]))

        contributors = []
        contributors.extend([i.user.login for i in issues_opened])
        contributors.extend([p.user.login for p in pulls_opened])
        contributors.extend([c.user.login for c in comments])
        contributors.extend([e.actor.login for e in issues_closes])
        contributors.extend([e.actor.login for e in pulls_closes])
        contributors = set(contributors)
        m['Contributors'] = (len(contributors),
                             len([c for c in contributors if c in members]))

        releases = [r for r in self.releases
                    if r.created(after=start, before=end)]
        m['Releases'] = (len(releases), None)

        return m

    def _fetch(self, apicall, apiargs={}, wrapper=None):
        things = apicall(per_page=100, **apiargs)
        last_page = self._api.last_page()
        if last_page > 0:
            things = pages(apicall, last_page, **apiargs).concat()

        if wrapper:
            for thing in things:
                thing.__class__ = wrapper

        return things


class GithubObject(AttrDict):

    def created(self, after=None, before=None):
        dt = datetime.strptime(self.created_at, _GITHUB_DATE_FORMAT)
        return (not after or dt > after) and (not before or dt < before)

    def updated(self, after=None, before=None):
        dt = datetime.strptime(self.updated_at, _GITHUB_DATE_FORMAT)
        return (not after or dt > after) and (not before or dt < before)


class Issue(GithubObject):

    _api = None

    def closed(self, after=None, before=None):
        if not self.closed_at:
            return False
        dt = datetime.strptime(self.closed_at, _GITHUB_DATE_FORMAT)
        return (not after or dt > after) and (not before or dt < before)

    def close(self, label=None, comment=None):
        if label:
            self._api.issues.add_labels(self.number, [label])
        if comment:
            self._api.issues.create_comment(self.number, comment)
        self._api.issues.update(self.number, state='closed')


class Commit(GithubObject):

    def created(self, after=None, before=None):
        dt = datetime.strptime(self.commit.author.date, _GITHUB_DATE_FORMAT)
        return (not after or dt > after) and (not before or dt < before)
