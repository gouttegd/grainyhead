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
