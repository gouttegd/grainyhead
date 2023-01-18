***********************
Working with old issues
***********************

GrainyHead provides two commands to work with “old” issues – issues that have
not been updated (no comments or addition/removal of an issue label) for a given
amount of time (by default, 365 days).


.. _listing-old-issues:

Listing old issues
------------------

The ``issues`` command list old issues in the repository. It produces a
Markdown-formatted table giving, for each issue, its title, the user who
authored it and whether that user is a known contributor to the repository, and
the user(s) to which the issue has been assigned, if any.

Use the ``--older-than`` option to change the duration after which an issue is
consider to be “old“. This option accepts:

* a plain date, written as ``YYYY-MM-DD`` or ``YYYY-MM``;
* a number of days, written as ``Xd`` or simply as ``X``;
* a number of weeks, written as ``Xw``;
* a number of months, written as ``Xm``;
* a number of years, written as ``Xy``;
* the value ``now``, representing the current date (would consider all issues as
  old).

With the ``--team NAME`` option, the command will indicate for each issue
whether the author is a member of the team *NAME*, instead of whether they are a
“known contributor”. This requires that the user account associated with the
access token is a member of the organisation the team belongs to and that the
token has the `read:org` permission.

The following example will list issues that have not been updated in the past
6 months and indicate whether their authors belong to the *elite* team:

.. code-block:: console

   $ grainyhead issues --older-than 6m --team elite


.. _closing-old-issues:

Closing old issues
------------------

The ``close`` command will automatically close all issues that are considered
“old” (the same issues that are listed by the ``issues`` command above). A label
``autoclosed-unfixed`` (which will be created if it didn’t already exist in the
repository) will be added to those issues.

As for the ``issues`` command, use the ``--older-than`` option to change the
threshold duration after which an issue is considered “old”.

If the ``--comment`` option is used on the command line, or if the configuration
file contains a ``close.comment`` option, a comment will be appended to each
issue before they are closed.

Use the ``--limit N`` option to only close the *N* oldest issues.

The issues that would be closed by the command are printed on the terminal and
an explicit confirmation is asked before the command proceeds with the actual
closing process. If the ``--dry-run`` option is used, the command only lists the
issues to be closed without going further.

The following example will close the 30 oldest issues that have not been
updated in the past 3 years:

.. code-block:: console

   $ grainyhead close --older-than 3y --limit 30 \
     --comment "This issue has been closed automatically."
