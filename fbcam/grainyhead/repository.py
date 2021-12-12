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

from ghapi.core import GhApi

from fbcam.grainyhead.providers import (MemoryRepositoryProvider,
                                        OnlineRepositoryProvider,
                                        RepositoryItemType)


class Repository(object):

    def __init__(self, owner, name, token=None):
        self._owner = owner
        self._api = GhApi(owner=owner, repo=name, token=token)
        self._provider = MemoryRepositoryProvider(
            OnlineRepositoryProvider(self._api))
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

    def get_metrics(self, start, end, team='__collaborators'):
        m = {}
        members = [m.login for m in self.get_team(team)]

        issues_opened = [i for i in self.all_issues
                         if i.created(after=start, before=end)]
        m['Issues opened'] = (len(issues_opened),
                              len([i for i in issues_opened
                                   if i.user.login in members]))

        # Get only the events created after the cutoff start date
        self._provider.get_data(RepositoryItemType.EVENTS, start)

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
