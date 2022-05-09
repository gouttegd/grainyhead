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


Default report
--------------

By default, the ``metrics`` command collects the number of events for the entire
repository during the reporting period, and breaks those numbers into two
categories depending on whether the events were caused by known contributors to
the repository (“internal” contributions) or from other users (“external”
contributions).

Here is an example of a default report:

.. code-block:: console

   $ grh metrics
   From 2021-09-02 to 2021-12-01
   
   | Event                | Total | Internal | Inte (%) | External | Exte (%) |
   | -------------------- | ----- | -------- | -------- | -------- | -------- |
   | Contributors         |    24 |       15 |    62.50 |        9 |    37.50 |
   | Issues opened        |    71 |       64 |    90.14 |        7 |     9.86 |
   | Issues closed        |    89 |       77 |    86.52 |       12 |    13.48 |
   | Pull requests opened |    86 |       68 |    79.07 |       18 |    20.93 |
   | Pull requests closed |    94 |       78 |    82.98 |       16 |    17.02 |
   | Pull requests merged |    79 |       65 |    82.28 |       14 |    17.72 |
   | Comments             |   476 |      412 |    86.55 |       64 |    13.45 |
   | Commits              |   232 |      201 |    86.64 |       31 |    13.36 |
   | Releases             |     4 |        4 |   100.00 |        0 |     0.00 |

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
    
The meaning of a selector can be inverted by prepending a ``!`` character. For
example, ``--selector !team:elite`` would collect all events originating from
users that are *not* members of the *elite* team.

The ``--selector`` option can be repeated as many times as needed to collect
metrics about different sets of events.

Each selector can be given a human-readable *NAME* to be displayed in the column
header, by appending ``AS NAME`` to the selector.

The ``user`` and ``label`` selectors accept a special syntactic sugar:
``user:*`` and ``label:*`` will collect events for all contributors and for all
labels in the repository, respectively. That is, ``--selector 'user:*'`` is
equivalent for ``--selector user:user1 --selector user:user2 ...``, for all
users *user1*, *user2*, ..., known to have contributed to the repository;
likewise, ``--selector 'label:*'`` is equivalent to ``--selector label:label1
--selector label:label2 ...`` for all labels *label1*, *label2*, ..., ever used
in the repository. This syntax is not compatible with the ``!`` and ``AS NAME``
constructions.

Here is an example of a custom report request:

.. code-block:: console

   $ grh metrics \
       --selector 'all AS Total' \
       --selector '!team:elite AS Others' \
       --selector 'label:bugfix AS Bugs'
   From 2021-11-09 to 2022-05-08
   
   | Event                | Total    | Others   | Othe (%) | Bugs     | Bugs (%) |
   | -------------------- | -------- | -------- | -------- | -------- | -------- |
   | Contributors         |       46 |       20 |    43.48 |       44 |    95.65 |
   | Issues opened        |      184 |      116 |    63.04 |      136 |    73.91 |
   | Issues closed        |      134 |      133 |    99.25 |      106 |    79.10 |
   | Pull requests opened |      200 |      193 |    96.50 |      196 |    98.00 |
   | Pull requests closed |      164 |      164 |   100.00 |      162 |    98.78 |
   | Pull requests merged |      139 |      139 |   100.00 |      138 |    99.28 |
   | Comments             |     1085 |      938 |    86.45 |        0 |     0.00 |
   | Commits              |      485 |      475 |    97.94 |        0 |     0.00 |
   | Releases             |        5 |        5 |   100.00 |        0 |     0.00 |

It prints the numbers of all events in the repository, the number of events
originating from users that are not members of the *elite* team, and the number
of events labelled with the *bugfix* label.


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
the human-readable name specified with the ``AS NAME`` syntax (as explained in
the previous section), if any. In any case, the title is truncated to 8
characters.

Here is an example of the effect of the ``AS NAME`` syntax:

.. code-block:: console

   $ grh metrics \
       --selector '!team:elite AS Others' \
       --selector 'label:bugfix'
   From 2021-11-09 to 2022-05-08
   
   | Event                | Others   | label:bu |
   | -------------------- | -------- | -------- |
   | Contributors         |       20 |       44 |
   | Issues opened        |      116 |      136 |
   | Issues closed        |      133 |      106 |
   | Pull requests opened |      193 |      196 |
   | Pull requests closed |      164 |      162 |
   | Pull requests merged |      139 |      138 |
   | Comments             |      938 |        0 |
   | Commits              |      475 |        0 |
   | Releases             |        5 |        0 |

As a convenience, if the *first* selector is the ``all`` selector, then for each
subsequent selector, an extra column is appended to give the proportion of
events corresponding to the selector relatively to all events:

.. code-block:: console

   $ grh metrics \
       --selector 'all AS Total' \
       --selector '!team:elite AS Others'
   From 2021-11-09 to 2022-05-08
   
   | Event                | Total    | Others   | Othe (%) |
   | -------------------- | -------- | -------- | -------- |
   | Contributors         |       46 |       20 |    43.48 |
   | Issues opened        |      184 |      116 |    63.04 |
   | Issues closed        |      134 |      133 |    99.25 |
   | Pull requests opened |      200 |      193 |    96.50 |
   | Pull requests closed |      164 |      164 |   100.00 |
   | Pull requests merged |      139 |      139 |   100.00 |
   | Comments             |     1085 |      938 |    86.45 |
   | Commits              |      485 |      475 |    97.94 |
   | Releases             |        5 |        5 |   100.00 | 


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
    specified with the ``AS NAME`` syntax, this column contains the same value
    as the second column, that is the selector itself).

The remaining columns are for the reported values. Their names should be
self-explanatory.

Here is an example of CSV output:

.. code-block:: console

   $ grh metrics --format csv \
       --selector 'all AS Total' \
       --selector '!team:elite AS Others' \
       --selector 'label:bugfix AS Bugs'
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

   $ grh metrics --format csv --from 1y --period 3m 
   Date,Selector,Selector name,Issues opened,Issues closed,Pull requests opened,Pull requests closed,Pull requests merged,Comments,Commits,Releases,Contributors
   2021-08-08,all,Total,90,509,88,84,62,927,200,4,26
   2021-11-08,all,Total,60,56,63,70,57,401,185,2,28
   2022-02-08,all,Total,54,70,75,76,66,465,224,2,29
   2022-05-08,all,Total,127,62,124,86,71,597,254,3,37
