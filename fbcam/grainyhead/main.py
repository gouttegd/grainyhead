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

from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
import sys

import click
from click_shell import shell
from ghapi.core import GhApi
from ghapi.page import pages
from IPython import embed

from fbcam.grainyhead import __version__

prog_name = "grh"
prog_notice = f"""\
{prog_name} {__version__}
Copyright © 2021 Damien Goutte-Gattat

This program is released under the GNU General Public License.
See the COPYING file or <http://www.gnu.org/licenses/gpl.html>.
"""


def die(msg):
    print(f"{prog_name}: {msg}", file=sys.stderr)
    sys.exit(1)


@shell(context_settings={'help_option_names': ['-h', '--help']},
       prompt="grh> ")
@click.option('--config', '-c', type=click.Path(exists=True),
              default='{}/config'.format(click.get_app_dir('grainyhead')),
              help="Path to an alternative configuration file.")
@click.option('--section', '-s', default='default',
              help="Name of the configuration file section to use.")
@click.version_option(version=__version__, message=prog_notice)
@click.pass_context
def grh(ctx, config, section):
    """Command-line tool for GitHub."""

    cfg = ConfigParser()
    cfg.read(config)

    if not cfg.has_section(section):
        die(f"No section {section} in configuration.")
    owner = cfg.get(section, 'user')
    repo = cfg.get(section, 'repo')
    token = cfg.get(section, 'token', fallback=None)

    api = GhApi(owner=owner, repo=repo, token=token)
    ctx.obj = api


@grh.command(name='issues')
@click.option('--older-than', default=365,
              help="""Only list issues that have not been updated for the
                      specified number of days (default=365).""")
@click.option('--team', default=None,
              help="""The name of a GitHub team, written as
                      <organisation>/<team>.""")
@click.pass_obj
def list_issues(api, older_than, team):
    """List open issues.
    
    This commands list open issues that have not been updated for a
    given amount of time.
    """

    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than)

    _ = api.issues.list_for_repo(per_page=100)
    issues = pages(api.issues.list_for_repo, api.last_page()).concat()
    issues = [i for i in issues if not hasattr(i, 'pull_request') and _issue_is_older(i, cutoff)]

    if team:
        organisation, team_name = team.split('/')
        members = api.teams.list_members_in_org(org=organisation, team_slug=team_name, per_page=100)
        member_names = [m.login for m in members]

    print("| Issue | Author | Team? | Assignee(s) |")
    print("| ----- | ------ | ----- | ----------- |")

    for issue in issues:
        assignees = ', '.join(['@[{}]({})'.format(a.login, a.html_url) for a in issue.assignees])
        if team:
            if issue.user.login in member_names:
                is_team = 'Yes'
            else:
                is_team = 'No'
        elif issue.author_association in ['OWNER', 'MEMBER', 'CONTRIBUTOR']:
            is_team = 'Yes'
        else:
            is_team = 'No'

        print(f"| [{issue.title}]({issue.html_url}) | @[{issue.user.login}]({issue.user.html_url}) | {is_team} | {assignees} |")


@grh.command(name='ipython')
@click.pass_obj
def python_shell(api):
    """Start an interactive Python shell.
    
    This commands starts a Python shell from where the GitHub API can be
    directly manipulated through the 'api' object. This is intended for
    testing purposes.
    """

    embed()


def _issue_is_older(issue, cutoff):
    update = datetime.strptime(issue.updated_at, '%Y-%m-%dT%H:%M:%S%z')
    return update < cutoff


if __name__ == '__main__':
    grh()
