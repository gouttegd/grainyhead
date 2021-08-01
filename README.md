GrainyHead - Helper tools for GitHub
====================================

GrainyHead is a set of Python scripts to work with GitHub repositories
from the command line.

The name comes from the fruit fly gene _grainyhead_ (_grh_).


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
on how to get an access token.

If the configuration file does not exist, you will be prompted for the
repository URL and your access token when you first invoke the program.


Main commands
-------------

Invoke `grh` with the `--help` option to get the list of available
commands. Invoke a command with that same option to get a detailled help
message for the command.

If called without any command, `grh` will enter into an interactive
shell mode, from which commands can be entered repeatedly without
leaving the program.


### Listing old issues in a repository

Use the `issues` command to list open issues that have not been updated
for a while (365 days by default):

```
$ grh issues
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


Copying
-------
GrainyHead is distributed under the terms of the GNU General Public
License, version 3 or higher. The full license is included in the
[COPYING file](COPYING) of the source distribution.
