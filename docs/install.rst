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
   $ cd grainyhead-0.3.2

GrainyHead requires the following Python dependencies to work:

* `click-shell <https://github.com/clarkperkins/click-shell>`_
* `ghapi <https://ghapi.fast.ai/>`_
* `python-dateutil <https://github.com/dateutil/dateutil>`_

Install those dependencies with ``pip``:

.. code-block:: console

   $ python -m pip install -r requirements.txt

Then build a *wheel* package and install it:

.. code-block:: console

   $ python setup.py bdist_wheel
   $ python -m pip install dist/grainyhead-0.3.2-py3-none-any.whl

To install the current development version (tip of the master branch), you may
either clone locally the repository and then proceed as above, or use *pip* to
install directly from GitHub:

.. code-block:: console

   $ python -m pip install -U git+https://github.com/gouttegd/grainyhead.git


Testing the installation
========================

Once installed, GrainyHead may be invoked from the command line by calling the
``grainyhead`` program. You can check whether it has been installed correctly by
running the following command:

.. code-block:: console

   $ grh --version
   grh (GrainyHead 0.3.2)
   Copyright © 2024 Damien Goutte-Gattat

   This program is released under the GNU General Public License.
   See the COPYING file or <http://www.gnu.org/licenses/gpl.html>.
