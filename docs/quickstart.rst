***************
Getting Started
***************

.. _new-conf:

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

   $ grainyhead
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
``grainyhead <command>``), in which case GrainyHead will perform the
corresponding task then quit. Otherwise, if no command is specified, you enter
into an interactive shell from which you can repeatedly run commands without
quitting GrainyHead.

Use the ``help`` command to get the list of available commands.

The main commands are:

``issues``
    :ref:`List old issues <listing-old-issues>` in the repository.
    
``close``
    :ref:`Close old issues <closing-old-issues>` in the repository.
    
``metrics``
    :doc:`Print some statistics <metrics>` about the repository.
