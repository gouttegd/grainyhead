*********************
Installing GrainyHead
*********************

As of now, GrainyHead is not yet available on the `Python Package Index`_, so
it has to be installed from source.

.. _Python Package Index: https://pypi.org/


Installing from source
======================

There is no formal release yet, so you need to clone the `Git repository`_:

.. _Git repository: https://github.com/gouttegd/grainyhead

.. code-block:: console

   $ git clone https://github.com/gouttegd/grainyhead.git
   $ cd grainyhead

GrainyHead requires the following Python dependencies to work:

* `click-shell <https://github.com/clarkperkins/click-shell>`_
* `ghapi <https://ghapi.fast.ai/>`_
* `dateutil <https://github.com/dateutil/dateutil>`_

Install those dependencies with ``pip``:

.. code-block:: console

   $ python -m pip install -r requirements.txt

Then build a *wheel* package and install it:

.. code-block:: console

   $ python setup.py bdist_wheel
   $ python -m pip install dist/grainyhead-0.1.0-py3-none-any.whl


Testing the installation
========================

Once installed, GrainyHead may be invoked from the command line by calling the
``grh`` program. You can check whether it has been installed correctly by
running the following command:

.. code-block:: console

   $ grh --version
   grh (GrainyHead 0.1.0)
   Copyright © 2021 Damien Goutte-Gattat

   This program is released under the GNU General Public License.
   See the COPYING file or <http://www.gnu.org/licenses/gpl.html>.
