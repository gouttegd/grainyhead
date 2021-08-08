***************
Getting Started
***************

Creating a configuration file
=============================

GrainyHead requires a configuration file listing the repositories to work
with. By default, it will look for a file named ``config`` under the directory
``$XDG_CONFIG_HOME/grainyhead`` or, on MacOS systems, under the directory
``~/Library/Application Support/grainyhead``.

When you first invoke GrainyHead, if no configuration file exists, you will be
prompted for the URL to the repository you want to work with and the *personal
access token* to authenticate on GitHub:

.. code-block:: console

   $ grh
   Repository name or URL: https://github.com/gouttegd/grainyhead
   Visit https://github.com/settings/tokens to create a personal access token
   Token: <personal access token>
   grh>

GrainyHead will then create an initial configuration with those values and
drop you into an interactive shell. Use the ``exit`` command (or ``^D``) at
any time to exit GrainyHead’s shell and get back to the system shell.


GrainyHead commands
===================

Each GrainyHead command can be invoked directly from the command line (with
``grh <command>``), in which case GrainyHead will perform the corresponding
task then quit. Otherwise, if no command is specified, you enter into an
interactive shell from which you can repeatedly run commands without quiting
GrainyHead.

Use the ``help`` command to get the list of available commands.


Listing old issues
------------------

The ``issues`` command list all issues that have not been updated for a given
amount of time (365 days by default). It produces a Markdown-formatted table
giving, for each issue, its title, the user who authored it and whether that
member is a known contributor to the repository, and the users to which the
issue has been assigned, if any.

With the ``--team`` option, the table will indicate whether the issue’s author
is a member of the specified team, instead of whether they are a “known
contributor”.

The following example will list issues that have not been updated in the past
6 months and indicate whether their authors belong to the *elite* team:

.. code-block:: console

   grh issues --older-than 6m --team elite


Closing old issues
------------------

The ``close`` command will automatically close all issues that have not been
updated for a given amount of time (365 days by default). A label
``autoclosed-unfixed`` (which will be created if it didn’t already exist in
the repository) will be added to those issues.

If the ``--comment`` option is used on the, or if the configuration file contains a
``close.comment`` option, a comment will be appended to each issues before
they are closed.

The command will list the issues that are to be closed and ask for
confirmation before proceeding with the closing.

Use the ``--limit N`` option to only close the *N* oldest issues.

The following example will close the 30 oldest issues that have not been
updated in the past 3 years:

.. code-block:: console

   grh close --older-than 3y --limit 30 \
     --comment "This issue has been closed automatically."
