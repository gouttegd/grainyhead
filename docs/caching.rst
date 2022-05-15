*******
Caching
*******

Because some of GrainyHead’s functions (especially the ``metrics`` command)
require fetching a lot of data from GitHub, by default a local cache is used.


Cache location
==============

The cache for a given repository is in the ``$XDG_DATA_HOME/grainhyhead/name``
directory, where *name* is the name of the repository section in GrainyHead’s
configuration file.


Default behaviour
=================

Any time GrainyHead needs some repository data, it looks them up in the file
cache first.

If there are no cached data, it fetches them from GitHub and writes them to the
cache before using them as intended.

If there are cached data, GrainyHead checks when they have last been updated. If
they are more than 30 days old, the cache is *refreshed*, meaning that new data
(data generated after the last update) are fetched from GitHub and appended to
the cache. If the cached data are less than 30 days old, then GrainyHead uses
those data without refreshing them.

This behaviour means that by default, any time GrainyHead is executed, and
unless the cache was empty (which happens when GrainyHead is executed for the
first time on a given repository), it will be ignorant of anything that happened
in the repository in the last 30 days.


Controlling the cache
=====================

The default behaviour described above can be changed using the ``caching``
option. That option can be specified either in a repository section of the
configuration file, or on the command line (before any subcommand). The value
specified on the command line, if any, overrides any value that may be set in
the configuration value.

This option can be used to change the number of days after which the cached data
are considered old and need refreshing. That number can be specified in several
ways:

* directly as a number of days, written as ``Xd`` or simply as ``X``;
* as a number of weeks, written as ``Xw``;
* as a number of months, written as ``Xm``;
* as a number of years, written as ``Xy``.

In addition, the option accepts a few special values to change more profoundly
the behaviour of the cache:

``disabled`` (or ``no-cache``)
	The cache is entirely disabled. All data are always downloaded from GitHub,
	and never written to disk.
	
``refresh`` (or ``always``)
    The cache is forcefully refreshed (new data are downloaded and appended to
    the cache), regardless of the age of the cached data.
    
``no-refresh`` (or ``never``)
    The cache is never refreshed, regardless of the the age of the cached data
    (refresh would still occur if the cache is empty).
    
``reset`` (or ``clear``)
    All data are forcefully downloaded from GitHub, replacing any cached data.


