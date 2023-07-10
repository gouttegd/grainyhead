******************
Repository metrics
******************

The ``metrics`` command collects the number of ”events” that occurred in the
repository over a given period of time (defaulting to the last 6 months).


Events collected
----------------

The command collects informations about the following events, if they occurred
during the reporting period:

* an issue has been opened;
* an issue has been closed;
* a pull request has been opened;
* a pull request has been closed;
* a pull request has been merged;
* a comment has been added to an issue or a pull request;
* a change has been committed;
* a release has been performed.

In addition, it also collects the number of individual contributors that caused
those events to occur.

Note that to gather those informations, the ``metrics`` command has to download
a potentially large amount of data from GitHub. Those data are cached on disk to
make subsequent calls faster, but the first time the ``metrics`` command is run
on any given repository, it can take several minutes for the command to complete
(depending on the size of the repository and the quality of the network
connection).


Default report
--------------

By default, the ``metrics`` command collects the number of events for the entire
repository during the reporting period, and breaks those numbers into two
categories depending on whether the events were caused by known contributors to
the repository (“internal” contributions) or from other users (“external”
contributions).

Here is an example of a default report:

.. code-block:: console

   $ grainyhead metrics
   From 2021-09-02 to 2021-12-01
   
   | Event | Total | Internal | Internal (%) | External | External (%) |
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

This report indicates, for example, that 24 users contributed to the repository
between September 2nd, 2021 and December 1st, 2021; 15 of them (62.5%) were
known contributors, the other 9 being external users.


Custom reports
--------------

Users can request custom reports with the ``--selector`` option, which allows to
specify which events should be reported.

The following selectors can be used:

``all``
    All events for the given reporting period, without any filtering.

``team:NAME``
    All events that were caused by users that are members of the *NAME* team.

``user:NAME``
    All events that were caused by the *NAME* user.

``label:NAME``
    All events about issues or pull requests tagged with the *NAME* label.
    
Note that the *NAME* value may contain spaces (as team names and labels can
contain spaces).

Selectors can be combined using the binary operators ``&``, ``|``, and ``^``:

``left & right``
	All events matching both the *left* and *right* selectors.

``left | right``
	All events matching either the *left* selector, the *right* selector, or
	both of them.

``left ^ right``
	All events matching one of the two selectors but not the other.

Parentheses can be used to group selectors and create more complex expressions:

``(A & B) | C``
	All events matching either the *A* and *B* selectors together, or the *C*
	selector, or all three of them.

``A ^ (B | C)``
	All events matching either the *A* selector, or (exclusive) the *B* or *C*
	selectors.

The unary operator ``!`` allows to invert the meaning of any selector (including
complex expressions) it is prepended to:

``!team:elite``
	All events originating from users that are *not* members of the *elite*
	team.

``!A & B``
    The complement of *A & B*, that is all the events that do not match *A* and
    *B* simultaneously.

Be careful that the ``!`` operator has a greater precedence than the binary
operators. As a result, the last example does *not* mean “all the events that do
not match *A* but that do match *B*! If this what you want, you need instead the
following expression: ``(!A) & B``.

Not all possible expressions do necessarily make sense. For example, ``user:A &
user:B`` (which theoretically means “all events originating from user *A* and
user *B*) would not match any event at all, since events in GitHub have only one
creator.

The ``--selector`` option can be repeated as many times as needed to collect
metrics about different sets of events.

Each selector can be given a human-readable *NAME* to be displayed in the column
header, by appending ``= NAME`` (or alternatively, ``AS name``, but that form is
deprecated and should not be used anymore) to the selector.

The ``user`` selector accepts a special syntactic sugar: ``user:*TEAM`` will
collect events for all users in team *TEAM* (or for all contributors if no team
is specified, that is if the selector is simply ``user:*``). That is,
``--selector 'user:*elite'`` is equivalent to ``--selector user:user1
--selector user:user2 ...`` where *user1*, *user2*, etc. are members of the
*elite* team.

The ``team`` selector similarly accepts the syntactic sugar ``team:*``, which
will collect events for all labels in the repository. That is, ``--selector
'label:*'`` is equivalent to ``--selector label:label` --selector label:label2
...`` for all labels *label1*, *label2*, etc. ever used in the repository.

Of note, only one wild-card selector may be used in any given expression: it is
not possible to use both ``user:*`` (with or without a team name) and
``label:*`` inside the same selector option.

Here is an example of a custom report request:

.. code-block:: console

   $ grainyhead metrics \
       --selector 'all = Total' \
       --selector '!team:elite = Others' \
       --selector 'label:bugfix = Bugs'
   From 2021-11-09 to 2022-05-08
   
   | Event | Total | Others | Others (%) | Bugs | Bugs (%) |
   | -------- | -------- | -------- | -------- | -------- | -------- |
   | Contributors | 46 | 20 | 43.48 | 44 | 95.65 |
   | Issues opened | 184 | 116 | 63.04 | 136 | 73.91 |
   | Issues closed | 134 | 133 | 99.25 | 106 | 79.10 |
   | Pull requests opened | 200 | 193 | 96.50 | 196 | 98.00 |
   | Pull requests closed | 164 | 164 | 100.00 | 162 | 98.78 |
   | Pull requests merged | 139 | 139 | 100.00 | 138 | 99.28 |
   | Comments | 1085 | 938 | 86.45 | 0 | 0.00 |
   | Commits | 485 | 475 | 97.94 | 0 | 0.00 |
   | Releases | 5 | 5 | 100.00 | 0 | 0.00 |

It prints the numbers of all events in the repository, the number of events
originating from users that are not members of the *elite* team, and the number
of events labelled with the *bugfix* label.


Special team names
------------------

The ``team`` selector will recognise a handful of special names, all starting with
``__``:

``team:__collaborators``
    All users that are registered as collaborators on the repository.
    
``team:__committers``
    All users who ever committed to the repository.
    
``team:__commenters``
    All users who ever opened a ticket or a PR or commented on a ticket or a PR.
    
``team:__contributors``
    All users who ever contributed anything (commit, issue, PR, comment) to the
    repository.
    
These names are also recognised by the ``user:*TEAM`` syntactic sugar. For
example, ``--selector 'user:*__committers'`` will be equivalent to ``--selector
user:user1 --selector user:user2 ...`` where *user1*, *user2*, etc. are users
who contributed commits to the repository. The special ``user:*`` sugar is
strictly equivalent to ``user:*__contributors``. 


Report formats
--------------

The ``metrics`` command can print the metrics in four different formats:
Markdown, JSON, CSV, and TSV. The format can be chosen with the ``--format``
option. The default format is Markdown.


Markdown format
^^^^^^^^^^^^^^^

See above for some examples of the Markdown output. Basically, it’s a Markdown
table where the first column indicates the events reported and the following
columns contain the number of said events for each selector specified.

The title of each column beyond the first one is either the selector itself, or
the human-readable name specified with the ``= NAME`` syntax (as explained in
the previous section), if any. In any case, the title is truncated to 8
characters.

Here is an example of the effect of the ``= NAME`` syntax:

.. code-block:: console

   $ grainyhead metrics \
       --selector '!team:elite = Others' \
       --selector 'label:bugfix'
   From 2021-11-09 to 2022-05-08
   
   | Event | Others | label:bugfix |
   | -------- | -------- | -------- |
   | Contributors | 20 | 44 |
   | Issues opened | 116 | 136 |
   | Issues closed | 133 | 106 |
   | Pull requests opened | 193 | 196 |
   | Pull requests closed | 164 | 162 |
   | Pull requests merged | 139 | 138 |
   | Comments | 938 | 0 |
   | Commits | 475 | 0 |
   | Releases | 5 | 0 |

As a convenience, if the *first* selector is the ``all`` selector, then for each
subsequent selector, an extra column is appended to give the proportion of
events corresponding to the selector relatively to all events:

.. code-block:: console

   $ grainyhead metrics \
       --selector 'all = Total' \
       --selector '!team:elite = Others'
   From 2021-11-09 to 2022-05-08
   
   | Event | Total | Others | Others (%) |
   | -------- | -------- | -------- | -------- |
   | Contributors | 46 | 20 | 43.48 |
   | Issues opened | 184 | 116 | 63.04 |
   | Issues closed | 134 | 133 | 99.25 |
   | Pull requests opened | 200 | 193 | 96.50 |
   | Pull requests closed | 164 | 164 | 100.00 |
   | Pull requests merged | 139 | 139 | 100.00 |
   | Comments | 1085 | 938 | 86.45 |
   | Commits | 485 | 475 | 97.94 |
   | Releases | 5 | 5 | 100.00 | 


JSON format
^^^^^^^^^^^

The JSON format is intended for easy consumption of the report by downstream
scripts. The output is a JSON dictionary containing two keys, as follows:

.. code-block:: json

   {
     "period": {
       "to": "2022-05-08",
       "from": "2011-11-09"
     },
     "contributions": [
       {
         "selector": "all",
         "results": {
           "contributors": 46,
           "issues": {
             "opened": 184,
             "closed": 134
           },
           "pull_requests": {
             "opened": 200,
             "closed": 164,
             "merged":139
           },
           "comments": 1085,
           "commits": 485,
           "releases": 5
         }
       }
     ]
   }

The ``period`` key should be self-explanatory and indicates the reporting period
covered by the report.

The ``contributions`` key is an array that contains as many items as selectors
were specified with the ``--selector`` option. Each item is itself a dictionary
with a ``selector`` key that indicates the selector corresponding to this part
of the report, and a ``results`` key containing the reported values.

When several selectors have been specified, the items in the ``contributions``
array are in the same order as the order of the ``--selector`` options on the
command line.


CSV and TSV formats
^^^^^^^^^^^^^^^^^^^

The CSV and TSV formats are intended for easy consumption by generic data
manipulation programs such as *LibreOffice Calc*, *R*, *Pandas*, etc. The two
formats are identical except for the separator character (comma or tab).

The resulting table contains 12 columns, the first three being:

``Date``
    The date of the end of the reporting period.

``Selector``
    The selector for the values in the rest of the current row.
    
``Selector name``
    The human-readable version of the selector name (if no such name has been
    specified with the ``= NAME`` syntax, this column contains the same value
    as the second column, that is the selector itself).

The remaining columns are for the reported values. Their names should be
self-explanatory.

Here is an example of CSV output:

.. code-block:: console

   $ grainyhead metrics --format csv \
       --selector 'all = Total' \
       --selector '!team:elite = Others' \
       --selector 'label:bugfix = Bugs'
   Date,Selector,Selector name,Issues opened,Issues closed,Pull requests opened,Pull requests closed,Pull requests merged,Comments,Commits,Releases,Contributors
   2022-05-08,all,Total,184,134,200,164,139,1085,485,5,46
   2022-05-08,!team:elite,Others,116,133,193,164,139,938,475,5,20
   2022-05-08,label:bugfix,Bugs,136,106,196,162,138,0,0,0,44


Reporting periods
-----------------

By default, the ``metrics`` command collects data for a period covering the last
six months.

Use the ``--from`` and ``--to`` options to set the beginning and end of the
reporting period, respectively. Both options accept the same syntax as the
``--older-than`` option describing in the :ref:`listing-old-issues` section.
The ``--from`` option additionally accepts the special value ``origin``, which
sets the beginning of the reporting period to the oldest possible date.

Use the ``--period`` option to break down the report in several periods of a
given duration. For example, with the default reporting period covering the last
six months, using ``--period monthly`` would create six consecutive reports, one
for each of the six months.

The ``--period`` option accepts:

* a number of days, written as ``Xd`` or simply ``X``;
* a number of weeks, written as ``Xw``;
* a number of months, written as ``Xm``;
* a number of years, written as ``Xy``;
* the value ``weekly``, equivalent to ``1w``;
* the value ``monthly``, equivalent to ``1m``;
* the value ``quarterly``, equivalent to ``3m``;
* the value ``yearly``, equivalent to ``1y``.

When using the `Markdown format`_, the reports for each period are simply
written out one after the other, in as many Markdown tables as there are periods
to report about.

In the `JSON format`_, using the ``--period`` option changes the type of the
top-level JSON object from a dictionary to an array, containing a dictionary
for each reporting period.

When using the `CSV and TSV formats`_, each period simply adds new rows to the
produced table. For each period, the value of the first column (``Date``) will
be set to the end of the period.

Here is an example of a report covering a global period of one year, broken down
in quarterly periods:

.. code-block:: console

   $ grainyhead metrics --format csv --from 1y --period 3m 
   Date,Selector,Selector name,Issues opened,Issues closed,Pull requests opened,Pull requests closed,Pull requests merged,Comments,Commits,Releases,Contributors
   2021-08-08,all,Total,90,509,88,84,62,927,200,4,26
   2021-11-08,all,Total,60,56,63,70,57,401,185,2,28
   2022-02-08,all,Total,54,70,75,76,66,465,224,2,29
   2022-05-08,all,Total,127,62,124,86,71,597,254,3,37
