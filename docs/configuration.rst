*************
Configuration
*************

Configuration file location
===========================

GrainyHead’s configuration file is looked for, by default, under the path
``$XDG_CONFIG_HOME/grainyhead/config``.

Another location may be specified using the ``-c`` or ``--config`` option.

If the configuration file (be it the default one or one specified with the
``-c`` option) does not exist when ``grh`` is called, the ``conf`` command will
automatically be invoked to prompt the user for enough informations to create a
minimal configuration file, as shown in :ref:`new-conf`.

Once a configuration file has been created, the ``conf`` command can be
explicitly used again to edit that file with the user’s preferred text editor.


Configuration file syntax
=========================

The configuration file’s general syntax is that of ``.ini`` files, as supported
by Python’s :py:mod:`configparser` module.

Briefly, the configuration file is organised into *sections* which start by a
bracked-enclosed header and contain key-value pairs.

You can use either a colon (``:``) or an equal sign (``=``) to separate keys and
values. Leading and trailing whitespaces are ignored, as well as lines starting
with either a semi-colon (``;``) or a number sign (``#``).


Configuration of repositories
=============================

Each section in the configuration file represents a GitHub repository work with.

There must be at least one section, which *must* be called ``default``. It
describes the repository that will be used by default.

To work with more repositories, add more sections to the configuration file,
giving each section a unique name. On the command line, select the section (and
therefore the repository) to use with the ``-s`` or ``--section`` option, which
expects the name of a configuration section.

Each section must have two keys:

``repository``
    This is the address to the GitHub repository. It can either be a full URL
    (e.g., ``https://github.com/gouttegd/grainyhead``), or more simply just the
    name of the GitHub account followed by the name of the repository (e.g.,
    ``gouttegd/grainyhead``).

``token``
    This is the *personal access token* needed to access the repository through
    the GitHub API. See `GitHub documentation`_ for details on how to obtain
    such a token.

.. _GitHub documentation: https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token

Note that even if you use a single token to access several repositories
(possibly all your repositories), the token must be explicitly specified in each
configuration section.

An optional key, ``caching``, can be used to control the file cache. See the
:doc:`Caching <caching>` section for details on that option.


Sample file
===========

Here is a sample configuration file for GrainyHead:

.. code-block:: ini

   [default]
   repository: https://github.com/gouttegd/grainyhead
   token: ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   
   [bio]
   repository: gouttegd/biopython
   token: ghp_YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY

With such a file, calling ``grainyheadh -s bio`` will make any subcommand work
on the *Biopython* repository. Calling simply ``grainyhead`` will make the
subcommands work on the *GrainyHead* repository.
