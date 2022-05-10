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

import json
from datetime import timedelta


class MetricsReporter(object):
    """Generate metrics about events in a repository."""

    def __init__(self, repository):
        """Create a new instance.
        
        :param repository: the repository to work with
        """

        self._repo = repository

    def get_report(self, selectors, start, end, period=None):
        selectors = self._expand_wildcard_selectors(selectors)

        if period is None:
            return self._get_report_for_period(selectors, start, end)
        else:
            done = False
            reports = []

            while not done:
                period_end = start + period - timedelta(days=1)
                reports.append(self._get_report_for_period(selectors, start,
                                                           period_end))

                if period_end > end:
                    done = True
                else:
                    start = start + period

            return reports

    def _get_report_for_period(self, selectors, start, end):
        rset = _MetricsReportSet(start, end)
        self._date_filter = DateRangeFilter(start, end)

        for selector in selectors:
            item_filter = self._get_filter_from_selector(selector)
            rset.contributions.append(self.get_single_report(item_filter))

        return rset

    def get_single_report(self, item_filter):
        """Get a single report object based on the given filter."""

        issues_opened = [i for i in self._repo.all_issues
                         if item_filter.filterIssue(i)]
        issues_closes = [e for e in self._repo.events
                         if e.event == 'closed'
                         and not hasattr(e.issue, 'pull_request')
                         and item_filter.filterEvent(e)]

        pulls_opened = [p for p in self._repo.all_pull_requests
                        if item_filter.filterIssue(p)]
        pulls_closes = [e for e in self._repo.events
                        if e.event == 'closed'
                        and hasattr(e.issue, 'pull_request')
                        and item_filter.filterEvent(e)]
        pulls_merged = [e for e in self._repo.events
                        if e.event == 'merged'
                        and item_filter.filterEvent(e)]

        comments = [c for c in self._repo.comments
                    if item_filter.filterComment(c)]

        commits = [c for c in self._repo.commits
                   if item_filter.filterCommit(c)]

        releases = [r for r in self._repo.releases
                    if item_filter.filterRelease(r)]

        contributors = []
        contributors.extend([i.user.login for i in issues_opened])
        contributors.extend([p.user.login for p in pulls_opened])
        contributors.extend([c.user.login for c in comments])
        contributors.extend([e.actor.login for e in issues_closes])
        contributors.extend([e.actor.login for e in pulls_closes])
        contributors = set(contributors)

        return _Report(str(item_filter), item_filter.name, [
            len(issues_opened),
            len(issues_closes),
            len(pulls_opened),
            len(pulls_closes),
            len(pulls_merged),
            len(comments),
            len(commits),
            len(releases),
            len(contributors)])

    def _expand_wildcard_selectors(self, selectors):
        if not True in ['*' in s for s in selectors]:
            return selectors

        expanded_selectors = []
        for selector in selectors:
            if selector == 'user:*':
                expanded_selectors.extend([f'user:{u}' for u in self._repo.contributors])
            elif selector == 'label:*':
                expanded_selectors.extend([f'label:{l}' for l in self._repo.labels])
            else:
                expanded_selectors.append(selector)

        return expanded_selectors

    def _get_filter_from_selector(self, selector, level=0):
        if ' AS ' in selector:
            selector, name = selector.split(' AS ')
        else:
            name = selector

        if selector[0] == '!':
            f = ComplementFilter(self._get_filter_from_selector(selector[1:], level + 1))
        elif selector == 'all':
            f = NullFilter()
        elif selector.startswith('team:'):
            team_slug = selector[5:]
            members = [m.login for m in self._repo.get_team(team_slug)]
            f = TeamFilter(team_slug, members)
        elif selector.startswith('user:'):
            user_name = selector[5:]
            f = UserFilter(user_name)
            if selector == name:
                name = f'@{user_name}'
        elif selector.startswith('label:'):
            label = selector[6:]
            f = LabelFilter(label)
            if selector == name:
                name = label
        else:
            f = NullFilter()

        if level == 0:
            return CombinedFilter(name, [self._date_filter, f])
        else:
            return f


class MetricsFormatter(object):
    """Write a MetricsReportSet object."""

    def write(self, metrics, output):
        pass

    @staticmethod
    def get_formatter(fmt):
        if fmt.lower() == 'markdown':
            return MarkdownMetricsFormatter()
        elif fmt.lower() == 'csv':
            return CsvMetricsFormatter()
        elif fmt.lower() == 'tsv':
            return CsvMetricsFormatter(sep='\t')
        else:
            # We default to JSON
            return JsonMetricsFormatter()


class JsonMetricsFormatter(MetricsFormatter):

    def write(self, metrics, output):
        if isinstance(metrics, list):
            d = [self._get_dict_for_period(m) for m in metrics]
        else:
            d = self._get_dict_for_period(metrics)
        json.dump(d, output, indent=2)

    def _get_dict_for_period(self, metrics):
        d = {
            'period': {
                'to': metrics.end_date.strftime('%Y-%m-%d'),
                'from': metrics.start_date.strftime('%Y-%m-%d')
                },
            'contributions': []
            }

        for report in metrics.contributions:
            c = {
                'selector': report.selector,
                'results': {
                    'contributors': report.contributors,
                    'issues': {
                        'opened': report.issues_opened,
                        'closed': report.issues_closed
                        },
                    'pull_requests': {
                        'opened': report.pull_requests_opened,
                        'closed': report.pull_requests_closed,
                        'merged': report.pull_requests_merged
                        },
                    'comments': report.comments,
                    'commits': report.commits,
                    'releases': report.releases
                    }
                }
            d['contributions'].append(c)

        return d


class MarkdownMetricsFormatter(MetricsFormatter):

    def write(self, reportset, output):
        if isinstance(reportset, list):
            for r in reportset:
                self._write_reportset(r, output)
        else:
            self._write_reportset(reportset, output)

    def _write_reportset(self, reportset, output):
        start = reportset.start_date
        end = reportset.end_date

        with_total = reportset.contributions[0].selector == 'all'

        output.write(f"From {start:%Y-%m-%d} to {end:%Y-%m-%d}\n")
        output.write("\n")

        output.write("| Event                |")
        if with_total:
            output.write(f" {reportset.contributions[0].name:8.8} |")
            for report in reportset.contributions[1:]:
                output.write(f" {report.name:8.8} | {report.name:4.4} (%) |")
            output.write("\n")
            output.write("| -------------------- | -------- |")
            for report in reportset.contributions[1:]:
                output.write(" -------- | -------- |")
            output.write("\n")
        else:
            for report in reportset.contributions:
                output.write(f" {report.name:8.8} |")
            output.write("\n")
            output.write("| -------------------- |")
            for report in reportset.contributions:
                output.write(" -------- |")
            output.write("\n")

        items = [
            "Contributors",
            "Issues opened",
            "Issues closed",
            "Pull requests opened",
            "Pull requests closed",
            "Pull requests merged",
            "Comments",
            "Commits",
            "Releases"
            ]

        for item in items:
            self._write_line(item, reportset.contributions, output, with_total)
        output.write('\n')

    def _write_line(self, label, reports, output, with_total):
        property_name = label.lower().replace(' ', '_')

        if with_total:
            total = getattr(reports[0], property_name)
            output.write(f"| {label:20} | {total: 8} |")

            for report in reports[1:]:
                value = getattr(report, property_name)
                if total > 0:
                    percent = value / total * 100
                else:
                    percent = 0.0
                output.write(f" {value:8} | {percent: 8.2f} |")
        else:
            output.write(f"| {label:20} |")
            for report in reports:
                value = getattr(report, property_name)
                output.write(f" {value:8} |")
        output.write("\n")


class CsvMetricsFormatter(MetricsFormatter):

    def __init__(self, sep=','):
        self._sep = sep

    def write(self, reportset, output):
        headers = ['Date', 'Selector', 'Selector name',
                   'Issues opened', 'Issues closed',
                   'Pull requests opened', 'Pull requests closed',
                   'Pull requests merged', 'Comments', 'Commits',
                   'Releases', 'Contributors']
        output.write(self._sep.join(headers))
        output.write('\n')

        if isinstance(reportset, list):
            for r in reportset:
                self._write_reportset(r, output)
        else:
            self._write_reportset(reportset, output)

    def _write_reportset(self, reportset, output):
        for report in reportset.contributions:
            values = [reportset.end_date.strftime('%Y-%m-%d'),
                      report.selector, report.name,
                      report.issues_opened, report.issues_closed,
                      report.pull_requests_opened, report.pull_requests_closed,
                      report.pull_requests_merged, report.comments,
                      report.commits, report.releases, report.contributors]
            output.write(self._sep.join([str(v) for v in values]))
            output.write('\n')


class _MetricsReportSet(object):
    """This object holds some metrics about events in a repository."""

    def __init__(self, start, end):
        """Create a new instance for the specified reporting period."""

        self._start = start
        self._end = end
        self._reports = []

    @property
    def start_date(self):
        """The beginning of the reporting period."""

        return self._start

    @property
    def end_date(self):
        """The end of the reporting period."""

        return self._end

    @property
    def contributions(self):
        """The individual contribution reports."""

        return self._reports


class _Report(object):
    """This object holds metrics computed from a given selector."""

    def __init__(self, selector, name, values):
        self._selector = selector
        self._name = name
        self._values = values

    @property
    def selector(self):
        return self._selector

    @property
    def name(self):
        return self._name

    @property
    def contributors(self):
        return self._values[8]

    @property
    def issues_opened(self):
        return self._values[0]

    @property
    def issues_closed(self):
        return self._values[1]

    @property
    def pull_requests_opened(self):
        return self._values[2]

    @property
    def pull_requests_closed(self):
        return self._values[3]

    @property
    def pull_requests_merged(self):
        return self._values[4]

    @property
    def comments(self):
        return self._values[5]

    @property
    def commits(self):
        return self._values[6]

    @property
    def releases(self):
        return self._values[7]


class ItemFilter(object):

    def filterIssue(self, issue):
        return self._filterItem(issue)

    def filterEvent(self, event):
        return self._filterItem(event)

    def filterComment(self, comment):
        return self._filterItem(comment)

    def filterCommit(self, commit):
        return self._filterItem(commit)

    def filterRelease(self, release):
        return self._filterItem(release)

    def _filterItem(self, _):
        return False

    @property
    def name(self):
        return str(self)


class NullFilter(ItemFilter):

    def _filterItem(self, _):
        return True

    def __str__(self):
        return 'all'


class DateRangeFilter(ItemFilter):

    def __init__(self, start, end):
        self._start = start
        self._end = end

    def __str__(self):
        return f'date:{self._start:%Y-%m-%d}..{self._end:%Y-%m-%d}'

    def _filterItem(self, item):
        return item.created(after=self._start, before=self._end)


class TeamFilter(ItemFilter):

    def __init__(self, team_name, members):
        self._members = members
        self._slug = team_name

    def __str__(self):
        return f'team:{self._slug}'

    def filterIssue(self, issue):
        return issue.user.login in self._members

    def filterEvent(self, event):
        return event.actor.login in self._members

    def filterComment(self, comment):
        return comment.user.login in self._members

    def filterCommit(self, commit):
        if commit.author is not None:
            return commit.author.login in self._members
        else:
            return False

    def filterRelease(self, release):
        return release.author.login in self._members


class UserFilter(TeamFilter):

    def __init__(self, user_name):
        TeamFilter.__init__(self, None, [user_name])

    def __str__(self):
        return f'user:{self._members[0]}'


class LabelFilter(ItemFilter):

    def __init__(self, label):
        self._label = label

    def __str__(self):
        return f'label:{self._label}'

    def filterIssue(self, issue):
        return self._label in [l.name for l in issue.labels]

    def filterEvent(self, event):
        return self._label in [l.name for l in event.issue.labels]


class ComplementFilter(ItemFilter):

    def __init__(self, inner_filter):
        self._filter = inner_filter

    def __str__(self):
        return f'!{str(self._filter)}'

    def filterIssue(self, issue):
        return not self._filter.filterIssue(issue)

    def filterEvent(self, event):
        return not self._filter.filterEvent(event)

    def filterComment(self, comment):
        return not self._filter.filterComment(comment)

    def filterCommit(self, commit):
        return not self._filter.filterCommit(commit)

    def filterRelease(self, release):
        return not self._filter.filterRelease(release)


class CombinedFilter(ItemFilter):

    def __init__(self, name, filters):
        self._name = name
        self._filters = filters

    def __str__(self):
        components = [str(f) for f in self._filters if not str(f).startswith('date:')]
        return ' & '.join(components)

    @property
    def name(self):
        return self._name

    def filterIssue(self, issue):
        return not False in [f.filterIssue(issue) for f in self._filters]

    def filterEvent(self, event):
        return not False in [f.filterEvent(event) for f in self._filters]

    def filterComment(self, comment):
        return not False in [f.filterComment(comment) for f in self._filters]

    def filterCommit(self, commit):
        return not False in [f.filterCommit(commit) for f in self._filters]

    def filterRelease(self, release):
        return not False in [f.filterRelease(release) for f in self._filters]

