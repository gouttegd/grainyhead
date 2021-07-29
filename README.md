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
user: <GitHub user name>
repo: <repository name>
token: <access token>
```

See [GitHub's documentation](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token)
on how to get an access token.


Listing old issues in a repository
----------------------------------

The only available command so far, `issues`, lists open issues that have
not been updated for a while (365 days by default):

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


Copying
-------
GrainyHead is distributed under the terms of the GNU General Public
License, version 3 or higher. The full license is included in the
[COPYING file](COPYING) of the source distribution.
