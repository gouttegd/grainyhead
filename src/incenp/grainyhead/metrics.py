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

import json
from datetime import timedelta

import pyparsing as pp

from .filtering import (
    NullFilter,
    DateRangeFilter,
    TeamFilter,
    UserFilter,
    LabelFilter,
    ComplementFilter,
    IntersectionFilter,
    UnionFilter,
    DifferenceFilter,
)


class MetricsReporter(object):
    """Generate metrics about events in a repository."""

    def __init__(self, repository):
        """Create a new instance.

        :param repository: the repository to work with
        """

        self._repo = repository
        self._selector_parser = None

    def get_report(self, selectors, start, end, period=None):
        selectors = self._expand_wildcard_selectors(selectors)

        if period is None:
            return self._get_report_for_period(selectors, start, end)
        else:
            done = False
            reports = []

            while not done:
                period_end = start + period - timedelta(days=1)
                reports.append(
                    self._get_report_for_period(selectors, start, period_end)
                )

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
            report = self.get_single_report(item_filter)
            if report.name.startswith('@') and report.all_contributions == 0:
                # Exclude reports for users with no contributions at all
                continue
            rset.contributions.append(report)

        return rset

    def get_single_report(self, item_filter):
        """Get a single report object based on the given filter."""

        issues_opened = [i for i in self._repo.all_issues if item_filter.filter(i)]
        issues_closes = [
            e
            for e in self._repo.events
            if e.event == 'closed'
            and not hasattr(e.issue, 'pull_request')
            and item_filter.filter(e)
        ]

        pulls_opened = [
            p for p in self._repo.all_pull_requests if item_filter.filter(p)
        ]
        pulls_closes = [
            e
            for e in self._repo.events
            if e.event == 'closed'
            and hasattr(e.issue, 'pull_request')
            and item_filter.filter(e)
        ]
        pulls_merged = [
            e
            for e in self._repo.events
            if e.event == 'merged' and item_filter.filter(e)
        ]

        comments = [c for c in self._repo.comments if item_filter.filter(c)]

        commits = [c for c in self._repo.commits if item_filter.filter(c)]

        releases = [r for r in self._repo.releases if item_filter.filter(r)]

        contributors = []
        contributors.extend([i.user.login for i in issues_opened])
        contributors.extend([p.user.login for p in pulls_opened])
        contributors.extend([c.user.login for c in comments])
        contributors.extend([e.actor.login for e in issues_closes if e.actor is not None])
        contributors.extend([e.actor.login for e in pulls_closes if e.actor is not None])
        contributors = set(contributors)

        return _Report(
            str(item_filter),
            item_filter.name,
            [
                len(issues_opened),
                len(issues_closes),
                len(pulls_opened),
                len(pulls_closes),
                len(pulls_merged),
                len(comments),
                len(commits),
                len(releases),
                len(contributors),
            ],
        )

    def _expand_wildcard_selectors(self, selectors):
        if not True in ['*' in s for s in selectors]:
            return selectors

        expanded_selectors = []
        for selector in selectors:
            if 'user:*' in selector:
                group = selector[6:].split(' ', 2)[0]
                real_group = group if len(group) > 0 else '__contributors'
                expanded_selectors.extend(
                    [
                        selector.replace('user:*' + group, f'user:{u}')
                        for u in self._repo.get_usernames(real_group)
                    ]
                )

            elif 'label:*' in selector:
                expanded_selectors.extend(
                    [
                        selector.replace('label:*', f'label:{l}')
                        for l in self._repo.labels
                    ]
                )
            else:
                expanded_selectors.append(selector)

        return expanded_selectors

    def _get_filter_from_selector(self, selector):
        return self._get_parser().parse_string(selector).as_list()[0]

    def _get_parser(self):
        if self._selector_parser is None:
            filter_value = pp.Combine(
                pp.Word(pp.alphanums + '-_')
                + (pp.White() + pp.Word(pp.alphanums + '-_'))[...]
            ).leaveWhitespace()
            team_filter = (
                (pp.Literal('team:') + filter_value)
                .set_parse_action(
                    lambda t: TeamFilter(t[1], self._repo.get_usernames(t[1]))
                )
                .leave_whitespace()
            )
            user_filter = (
                (pp.Literal('user:') + filter_value)
                .set_parse_action(lambda t: UserFilter(t[1]))
                .leave_whitespace()
            )
            label_filter = (
                (pp.Literal('label:') + filter_value)
                .set_parse_action(lambda t: LabelFilter(t[1]))
                .leave_whitespace()
            )
            all_filter = pp.Literal('all').set_parse_action(lambda _: NullFilter())
            filter_item = all_filter | team_filter | user_filter | label_filter

            expression = pp.Forward()
            complement_filter = (
                (pp.Literal("!") + expression)
                .set_parse_action(lambda t: ComplementFilter(t[1]))
                .leave_whitespace()
            )
            atom = (
                filter_item
                | complement_filter
                | (pp.Literal('(').suppress() + expression + pp.Literal(')').suppress())
            )
            operator = pp.one_of(['&', '|', '^'])
            expression <<= (atom + operator + pp.White().suppress())[0, 1] + atom
            expression.set_parse_action(self._expression_action)

            selector = (
                expression
                + (
                    (pp.Literal('AS') | pp.Literal('=')).suppress() + pp.Word(pp.alphas)
                )[0, 1]
                + pp.StringEnd()
            ).set_parse_action(self._selector_action)
            self._selector_parser = selector
        return self._selector_parser

    def _selector_action(self, tokens):
        if len(tokens) == 2:
            name = tokens[1]
        else:
            name = tokens[0].name
        return NamedFilter(name, [self._date_filter, tokens[0]])

    def _expression_action(self, tokens):
        if len(tokens) == 3:
            if tokens[1] == '&':
                return IntersectionFilter([tokens[0], tokens[2]])
            elif tokens[1] == '|':
                return UnionFilter([tokens[0], tokens[2]])
            elif tokens[1] == '^':
                return DifferenceFilter([tokens[0], tokens[2]])
            else:
                # should not happen
                return NullFilter()
        else:
            return tokens[0]


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
                'from': metrics.start_date.strftime('%Y-%m-%d'),
            },
            'contributions': [],
        }

        for report in metrics.contributions:
            c = {
                'selector': report.selector,
                'results': {
                    'contributors': report.contributors,
                    'issues': {
                        'opened': report.issues_opened,
                        'closed': report.issues_closed,
                    },
                    'pull_requests': {
                        'opened': report.pull_requests_opened,
                        'closed': report.pull_requests_closed,
                        'merged': report.pull_requests_merged,
                    },
                    'comments': report.comments,
                    'commits': report.commits,
                    'releases': report.releases,
                },
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

        output.write("| Event |")
        if with_total:
            output.write(f" {reportset.contributions[0].name} |")
            for report in reportset.contributions[1:]:
                output.write(f" {report.name} | {report.name} (%) |")
            output.write("\n")
            output.write("| -------- | -------- |")
            for report in reportset.contributions[1:]:
                output.write(" -------- | -------- |")
            output.write("\n")
        else:
            for report in reportset.contributions:
                output.write(f" {report.name} |")
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
            "Releases",
        ]

        for item in items:
            self._write_line(item, reportset.contributions, output, with_total)
        output.write('\n')

    def _write_line(self, label, reports, output, with_total):
        property_name = label.lower().replace(' ', '_')

        if with_total:
            total = getattr(reports[0], property_name)
            output.write(f"| {label} | {total} |")

            for report in reports[1:]:
                value = getattr(report, property_name)
                if total > 0:
                    percent = value / total * 100
                else:
                    percent = 0.0
                output.write(f" {value} | {percent: .2f} |")
        else:
            output.write(f"| {label} |")
            for report in reports:
                value = getattr(report, property_name)
                output.write(f" {value} |")
        output.write("\n")


class CsvMetricsFormatter(MetricsFormatter):
    def __init__(self, sep=','):
        self._sep = sep

    def write(self, reportset, output):
        headers = [
            'Date',
            'Selector',
            'Selector name',
            'Issues opened',
            'Issues closed',
            'Pull requests opened',
            'Pull requests closed',
            'Pull requests merged',
            'Comments',
            'Commits',
            'Releases',
            'Contributors',
        ]
        output.write(self._sep.join(headers))
        output.write('\n')

        if isinstance(reportset, list):
            for r in reportset:
                self._write_reportset(r, output)
        else:
            self._write_reportset(reportset, output)

    def _write_reportset(self, reportset, output):
        for report in reportset.contributions:
            values = [
                reportset.end_date.strftime('%Y-%m-%d'),
                report.selector,
                report.name,
                report.issues_opened,
                report.issues_closed,
                report.pull_requests_opened,
                report.pull_requests_closed,
                report.pull_requests_merged,
                report.comments,
                report.commits,
                report.releases,
                report.contributors,
            ]
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

    @property
    def all_contributions(self):
        return sum(self._values)


class NamedFilter(IntersectionFilter):
    def __init__(self, name, filters):
        IntersectionFilter.__init__(self, filters)
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        components = [str(f) for f in self._filters if not str(f).startswith('date:')]
        return ' & '.join(components)
