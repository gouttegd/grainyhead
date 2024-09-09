*********************
Installing GrainyHead
*********************

Installing from PyPI
====================

Packages for GrainyHead are published on the `Python Package Index`_ under the
name ``grainyhead``. To install the latest version from PyPI:

.. _Python Package Index: https://pypi.org/project/grainyhead/

.. code-block:: console

   $ python -m pip install -U grainyhead


Installing from source
======================

You may download a release tarball from the `homepage`_ or from the
`release page`_, and then proceed to a manual installation:

.. _homepage: https://incenp.org/dvlpt/grainyhead.html
.. _release page: https://github.com/gouttegd/grainyhead/releases

.. code-block:: console

   $ tar zxf grainyhead-0.3.2.tar.gz
   $ python -m pip install ./grainyhead-0.3.2

(You may want/need to do that in a virtual environment, to avoid messing
with your system packages.)

To install the current development version (tip of the master branch), you may
either clone locally the repository and then proceed as above, or use *pip* to
install directly from GitHub:

.. code-block:: console

   $ python -m pip install -U git+https://github.com/gouttegd/grainyhead.git

GrainyHead requires the following Python dependencies to work:

* `click-shell <https://github.com/clarkperkins/click-shell>`_
* `ghapi <https://ghapi.fast.ai/>`_
* `python-dateutil <https://github.com/dateutil/dateutil>`_
* `pyparsing <https://github.com/pyparsing/pyparsing/>`_

They should automatically be installed by `pip` as needed.


Testing the installation
========================

Once installed, GrainyHead may be invoked from the command line by calling the
``grainyhead`` program. You can check whether it has been installed correctly by
running the following command:

.. code-block:: console

   $ grainyhead --version
   grainyhead (GrainyHead 0.3.2)
   Copyright © 2024 Damien Goutte-Gattat

   This program is released under the GNU General Public License.
   See the COPYING file or <http://www.gnu.org/licenses/gpl.html>.
