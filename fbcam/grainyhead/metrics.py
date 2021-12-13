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

import json


class MetricsFormatter(object):
    """Writes a report from a metrics dictionary."""

    def write(self, metrics, output):
        pass

    @staticmethod
    def get_formatter(fmt):
        if fmt.lower() == 'markdown':
            return MarkdownMetricsFormatter()
        else:
            # We default to JSON
            return JsonMetricsFormatter()


class JsonMetricsFormatter(MetricsFormatter):

    def write(self, metrics, output):
        json.dump(metrics, output, indent=2)


class MarkdownMetricsFormatter(MetricsFormatter):

    def write(self, metrics, output):
        # FIXME: I hate this code as much as I hate the
        # code from repository.get_metrics...
        start = metrics['period']['from']
        end = metrics['period']['to']

        output.write(f"From {start} to {end}\n")
        output.write("\n")
        output.write("| Event                | Total | Internal | External | Ext. (%) |\n")
        output.write("| -------------------- | ----- | -------- | -------- | -------- |\n")

        contribs = metrics['contributions']

        self._write_item("Issues opened",
                         contribs['all']['issues']['opened'],
                         contribs['internal']['issues']['opened'],
                         contribs['external']['issues']['opened'],
                         output)
        self._write_item("Issues closed",
                         contribs['all']['issues']['closed'],
                         contribs['internal']['issues']['closed'],
                         contribs['external']['issues']['closed'],
                         output)

        self._write_item("Pull requests opened",
                         contribs['all']['pull requests']['opened'],
                         contribs['internal']['pull requests']['opened'],
                         contribs['external']['pull requests']['opened'],
                         output)
        self._write_item("Pull requests closed",
                         contribs['all']['pull requests']['closed'],
                         contribs['internal']['pull requests']['closed'],
                         contribs['external']['pull requests']['closed'],
                         output)
        self._write_item("Pull requests merged",
                         contribs['all']['pull requests']['merged'],
                         contribs['internal']['pull requests']['merged'],
                         contribs['external']['pull requests']['merged'],
                         output)

        self._write_item("Comments",
                         contribs['all']['comments'],
                         contribs['internal']['comments'],
                         contribs['external']['comments'],
                         output)

        self._write_item("Commits",
                         contribs['all']['commits'],
                         contribs['internal']['commits'],
                         contribs['external']['commits'],
                         output)

        self._write_item("Contributors",
                         metrics['contributors']['total'],
                         metrics['contributors']['internal'],
                         metrics['contributors']['external'],
                         output)

        self._write_item("Releases",
                         contribs['all']['releases'],
                         None, None, output)

    def _write_item(self, label, total, internal, external, output):
        output.write(f"| {label:20} | {total: 5} ")
        if total > 0 and internal is not None:
            percent = external / total * 100
            output.write(f"| {internal: 8} | {external: 8} | {percent: 8.2f} |\n")
        else:
            output.write("|          |          |          |\n")

