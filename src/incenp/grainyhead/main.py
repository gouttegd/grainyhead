# grainyhead - Helper tools for GitHub
# Copyright © 2021,2022,2023,2024,2025 Damien Goutte-Gattat
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

import os
import re
import sys
from configparser import ConfigParser
from datetime import datetime, timedelta
from random import randint
from time import sleep
from typing import Any, Generator, Optional

import click
from click_shell import shell
from ghapi.core import GhApi  # type: ignore
from pyparsing import ParseException

from . import __version__
from .caching import CachePolicy
from .metrics import MetricsFormatter, MetricsReporter
from .providers import FileRepositoryProvider, OnlineRepositoryProvider
from .repository import IssueItem, Repository
from .util import Date, Interval

prog_name = "grh"
prog_notice = f"""\
{prog_name} (GrainyHead {__version__})
Copyright © 2025 Damien Goutte-Gattat

This program is released under the GNU General Public License.
See the COPYING file or <http://www.gnu.org/licenses/gpl.html>.
"""


def die(msg: str) -> None:
    print(f"{prog_name}: {msg}", file=sys.stderr)
    sys.exit(1)


def _parse_github_url(url: str) -> tuple[str, str]:
    m = re.match("(https?://github.com/)?([^/]+)/([^/.]+)", url)
    if not m:
        die(f"Invalid GitHub repository: {url}.")
        assert False

    return (m.groups()[1], m.groups()[2])


class GrhContext(object):
    _repo: Optional[Repository]
    _cache_policy: Optional[CachePolicy]

    def __init__(self, config_file: str, section: str = "default"):
        self._config_file = config_file
        self._name = section

        self._config = ConfigParser()
        self._has_config = len(self._config.read(config_file)) > 0

        self._repo = None
        self._cache_policy = None

    def reset(
        self,
        section: str = "default",
        config_file: Optional[str] = None,
        options: dict[str, Any] = {},
    ):
        self._repo = None
        self._name = section

        if config_file:
            self._config.clear()
            self._config_file = config_file
            self._has_config = len(self._config.read(config_file)) > 0
        elif options:
            self._config.clear()
            self._config.add_section(section)
            for key, value in options.items():
                self._config.set(section, key, value)
            self._has_config = True

    def get_option(self, key: str, fallback: Any = None) -> Any:
        return self._config.get(self._name, key, fallback=fallback)

    @property
    def repository(self) -> Repository:
        if not self._repo:
            repo_url = self._config.get(self._name, "repository")
            owner, repo = _parse_github_url(repo_url)
            token = self._config.get(self._name, "token", fallback=None)
            api = GhApi(owner=owner, repo=repo, org=owner, token=token)
            backend = FileRepositoryProvider(
                self.cache_dir, OnlineRepositoryProvider(api), self.cache_policy
            )
            self._repo = Repository(api, backend)
        return self._repo

    @property
    def has_config(self) -> bool:
        return self._has_config

    @property
    def config_file(self) -> str:
        return self._config_file

    @property
    def config(self) -> ConfigParser:
        return self._config

    @property
    def cache_policy(self) -> CachePolicy:
        if self._cache_policy is not None:
            return self._cache_policy
        else:
            p = CachePolicy.from_string(self.get_option("caching", "30d"))
            if p is None:
                die("Invalid cache policy")
                assert False
            return p

    @cache_policy.setter
    def cache_policy(self, policy: CachePolicy) -> None:
        self._cache_policy = policy

    @property
    def cache_dir(self) -> str:
        xdg_data_dir = os.getenv(
            "XDG_DATA_HOME", os.path.join(os.getenv("HOME", "~"), ".local", "share")
        )
        return os.path.join(xdg_data_dir, "grainyhead", self._name)


@shell(context_settings={"help_option_names": ["-h", "--help"]}, prompt="grh> ")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=False),
    default="{}/config".format(click.get_app_dir("grainyhead")),
    help="Path to an alternative configuration file.",
)
@click.option(
    "--section",
    "-s",
    default="default",
    help="Name of the configuration file section to use.",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable the file cache (deprecated: use --caching=disabled instead).",
)
@click.option(
    "--caching",
    type=CachePolicy.ClickType,
    default=None,
    help="Set the caching policy.",
)
@click.version_option(version=__version__, message=prog_notice)
@click.pass_context
def grh(ctx, config: str, section: str, no_cache: bool, caching: CachePolicy):
    """Command-line tool for GitHub."""

    context = GrhContext(config, section)
    if no_cache:
        caching = CachePolicy.DISABLED
    if caching is not None:
        context.cache_policy = caching
    ctx.obj = context
    if not context.has_config:
        ctx.invoke(conf)


@grh.command(name="issues")
@click.option(
    "--older-than",
    "cutoff",
    default="1y",
    type=Date,
    help="""Only list issues that have not been updated since the specified date
            or for the specified duration (default=1y, or one year ago).""",
)
@click.option(
    "--team",
    default="__collaborators",
    metavar="NAME",
    help="The name of a GitHub team.",
)
@click.pass_obj
def list_issues(grh: GrhContext, cutoff: datetime, team: str) -> None:
    """List open issues.

    This commands list open issues that have not been updated for a
    given amount of time.
    """

    repo = grh.repository

    issues = [i for i in repo.issues if i.updated(before=cutoff)]
    members = [m.login for m in repo.get_team(team)]

    print("| Issue | Author | Team? | Assignee(s) |")
    print("| ----- | ------ | ----- | ----------- |")

    for issue in issues:
        assignees = ", ".join(
            ["@[{}]({})".format(a.login, a.html_url) for a in issue.assignees]
        )
        is_team = "Yes" if issue.user.login in members else "No"

        print(
            f"| [{issue.title}]({issue.html_url}) | @[{issue.user.login}]({issue.user.html_url}) | {is_team} | {assignees} |"
        )


@grh.command(name="close")
@click.option(
    "--older-than",
    "cutoff",
    default="1y",
    type=Date,
    help="""Close issues that have not been updated since the specified date
            or for the specified duration (default=1y, or one year ago).""",
)
@click.option(
    "--comment",
    "-c",
    default=None,
    help="Text of the comment to add to the closed issues.",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    default=False,
    help="List issues that would be closed without actually closing them.",
)
@click.option(
    "--limit", "-l", default=-1, metavar="N", help="Only close the N oldest issues."
)
@click.pass_obj
def auto_close(
    grh: GrhContext, comment: str, cutoff: datetime, dry_run: bool, limit: int
) -> None:
    """Close old issues.

    This command automatically closes issues that have not been updated
    for a given amount of time.
    """

    repo = grh.repository

    repo.create_label(
        "autoclosed-unfixed", "ff7000", "This issue has been closed automatically."
    )

    if not comment:
        comment = grh.get_option("close.comment", fallback=None)

    issues = [i for i in reversed(repo.issues) if i.updated(before=cutoff)]
    if limit != -1:
        issues = issues[:limit]

    click.echo_via_pager(_list_closable_issues(issues))
    if comment:
        click.echo(f"Closing with comment: {comment}")
    if dry_run or not click.confirm("Proceed?"):
        return

    with click.progressbar(issues, item_show_func=_show_closing_issue) as bar:
        for issue in bar:
            repo.close_issue(issue, "autoclosed-unfixed", comment)

            # GitHub's documentation says that requests that trigger
            # notifications (such as adding a comment to an issue)
            # should be issued "at a reasonable pace", but does not
            # elaborate on what a "reasonable pace" is.
            # We try here to wait for anything between 2 and 10 seconds
            # between requests.
            sleep(randint(2, 10))


def _list_closable_issues(issues: list[IssueItem]) -> Generator[str]:
    yield f"The following {len(issues)} issues are about to be closed:\n"
    for issue in issues:
        last_update, _ = issue.updated_at.split("T")
        yield f"{issue.number}: last update {last_update}: {issue.title}\n"


def _show_closing_issue(issue: Optional[IssueItem] = None) -> str:
    if issue:
        return f"Closing issue #{issue.number}"
    else:
        return ""


@grh.command()
@click.option(
    "--from",
    "start",
    type=Date,
    default="6m",
    help="""Set the beginning of the reporting period.
                      Default to 6m (6 months ago).""",
)
@click.option(
    "--to",
    "end",
    type=Date,
    default="now",
    help="""Set the end of the reporting period.
                      Default to now.""",
)
@click.option(
    "--team",
    default="__collaborators",
    metavar="NAME",
    help="The name of a GitHub team.",
)
@click.option(
    "--selector",
    "-s",
    multiple=True,
    default=[],
    metavar="SELECTOR",
    help="Select a subset of repository events.",
)
@click.option(
    "--format",
    "-f",
    "fmt",
    default="markdown",
    type=click.Choice(["json", "markdown", "csv", "tsv"]),
    help="Write output in the specified format.",
)
@click.option(
    "--period",
    "-p",
    type=Interval,
    default=None,
    help="Break down the metrics per periods of the specified duration.",
)
@click.pass_obj
def metrics(
    grh: GrhContext,
    start: datetime,
    end: datetime,
    team: str,
    selector: list[str],
    fmt: str,
    period: timedelta,
):
    """Get repository metrics.

    This command collects and prints the number of repository events
    (such as the opening and closing of issues, commits, etc.) that
    occurred over a given period of time, as well as the number of
    individual contributors that caused those events.
    """

    reporter = MetricsReporter(grh.repository)
    if len(selector) == 0:
        selector = [
            "all = Total",
            f"team:{team} = Internal",
            f"!team:{team} = External",
        ]

    try:
        metrics = reporter.get_report(selector, start, end, period)
    except ParseException as err:
        print(f"Invalid selector: {err.line}")
        print(f"Column {err.column:<9}: " + " " * (err.column - 1) + "^")
        return

    formatter = MetricsFormatter.get_formatter(fmt)
    formatter.write(metrics, sys.stdout)


@grh.command()
@click.pass_obj
def conf(grh: GrhContext) -> None:
    """Edit the configuration.

    This command either creates a new basic configuration file for use
    with a repository or starts a text editor to edit the current
    configuration file if it already exists.
    """

    if grh.has_config:
        click.termui.edit(filename=grh.config_file)
        grh.reset(config_file=grh.config_file)
    else:
        opts = {}
        opts["repository"] = click.termui.prompt("Repository name or URL")

        click.echo(
            "Visit https://github.com/settings/tokens to create "
            "a personal access token."
        )
        opts["token"] = click.termui.prompt("Token")
        grh.reset(options=opts)

        with open(grh.config_file, "w") as f:
            grh.config.write(f)


@grh.command()
@click.option(
    "--cache-stats",
    is_flag=True,
    default=False,
    help="Show stats about the local cache.",
)
@click.pass_obj
def debug(grh: GrhContext, cache_stats: bool) -> None:
    """Print various informations for debugging."""

    if cache_stats:
        grh.cache_policy = CachePolicy.NO_REFRESH
        for item in [
            "issues",
            "all_issues",
            "pull_requests",
            "all_pull_requests",
            "comments",
            "events",
            "commits",
            "releases",
            "labels",
        ]:
            items = getattr(grh.repository, item)
            n = len(items)
            n_unique = len(set(items))
            if n_unique != n:
                print(f"{item}: {n} (unique: {n_unique})")
            else:
                print(f"{item}: {n}")


try:
    from IPython import start_ipython

    @grh.command(name="ipython")
    @click.pass_obj
    def python_shell(grh: GrhContext) -> None:
        """Start an interactive Python shell.

        This commands starts a Python shell from where the GitHub API
        can be directly manipulated through the 'api' object. This is
        intended for testing purposes.
        """

        start_ipython(
            argv=[], user_ns={"api": grh.repository._api, "repo": grh.repository}
        )

except ImportError:
    pass

if __name__ == "__main__":
    grh()
