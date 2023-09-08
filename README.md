[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8329980.svg)](https://doi.org/10.5281/zenodo.8329980)

GrainyHead - Helper tools for GitHub
====================================

GrainyHead is a set of Python scripts to work with GitHub repositories
from the command line.

The name comes from the fruit fly gene _grainyhead_ (_grh_).


Features
--------
Currently, GrainyHead allows to:

* list “old” issues (issues that have not been updated for a while) in a
  repository;
* automatically close said “old” issues;
* obtain some metrics about what happened in a repository (e.g. how many
  issues were opened, how many pull requests were merged, how many
  comments were added, etc.).


Configuration
-------------
GrainyHead needs a configuration file. The default configuration file is
`$XDG_CONFIG_HOME/grainyhead/config` on GNU/Linux and similar systems,
or `~/Library/Application Support/grainyhead/config` on Mac OS. Another
location may be specified with the `-c` option.

The configuration file uses the INI-style format where each section
describes a repository to work with. Here is a minimal configuration:

```
[default]
repository: https://github.com/<GitHub owner name>/<repository name>
token: <access token>
```

See [GitHub's documentation](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token)
on how to get an access token. Note that some features of GrainyHead
require that the token has the `read:org` permission.

If the configuration file does not exist, you will be prompted for the
repository URL and your access token when you first invoke the program.


Usage
-----
Invoke `grainyhead` with the `--help` option to get the list of
available commands. Invoke a command with that same option to get a
detailled help message for the command.

If called without any command, `grainyhead` will enter into an
interactive shell mode, from which commands can be entered repeatedly
without leaving the program.


### Listing old issues in a repository

Use the `issues` command to list open issues that have not been updated
for a while (365 days by default):

```
$ grainyhead issues
```

The output is a Markdown-style table containing, for each issue, its
name, its author, a value indicating whether the author is a known
contributor to the repository, and the names of any user(s) assigned to
take care of the issue.

Use the `--team` option to specify the name of the GitHub team from the
organisation that owns the repository. The command will then indicate
for each issue whether its author is a member of that team.


### Closing old issues in a repository

The `close` command will automatically close all issues that have not
been updated for a while (365 days by default).

Each issue to be closed with be tagged with `autoclosed-unfixed` and a
comment will be added to explain that the issue has been closed
automatically.


### Listing repository metrics

The `metrics` command will list some statistics about the repository
over a given period of time:

```
$ grainyhead metrics
From 2021-09-02 to 2021-12-01

| Event | Total | Internal | Internal (%) | External | Externam (%) |
| -------- | -------- | -------- | -------- | -------- | -------- |
| Contributors | 24 | 15 | 62.50 | 9 | 37.50 |
| Issues opened | 71 | 64 | 90.14 | 7 | 9.86 |
| Issues closed | 89 | 77 | 86.52 | 12 | 13.48 |
| Pull requests opened | 86 | 68 | 79.07 | 18 | 20.93 |
| Pull requests closed | 94 | 78 | 82.98 | 16 | 17.02 |
| Pull requests merged | 79 | 65 | 82.28 | 14 | 17.72 |
| Comments | 476 | 412 | 86.55 | 64 | 13.45 |
| Commits | 232 | 201 | 86.64 | 31 | 13.36 |
| Releases | 4 | 4 | 100.00 | 0 | 0.00 |
```


Copying
-------
GrainyHead is distributed under the terms of the GNU General Public
License, version 3 or higher. The full license is included in the
[COPYING file](COPYING) of the source distribution.


Homepage and repository
-----------------------

The project is located at <https://incenp.org/dvlpt/grainyhead.html>
with the manual at <https://incenp.org/dvlpt/grainyhead/index.html>.
The source code is available in a Git repository at
<https://github.com/gouttegd/grainyhead>.
