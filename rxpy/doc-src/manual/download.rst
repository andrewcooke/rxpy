
.. _install:

Download And Installation
=========================

RXPY is available for Python 2.6+.  It will soon support 3+ too.  


Installation With Distribute / Setuptools (easy_install)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::

   The source is more likely to be up-to-date (and consistent with the web
   documentation) than the current release.  I am not making regular releases
   until the project is a little more mature.

   However, the 0.0.0 release `does` work correctly as a regexp engine.

`Distribute <http://pypi.python.org/pypi/distribute>`_ and `setuptools
<http://pypi.python.org/pypi/setuptools>`_ are very similar, and either will
install RXPY on Python 2.6.  However, I recommend using `distribute
<http://pypi.python.org/pypi/distribute>`_ since it will also work with Python
3 (when RXPY runs there) and appears to be better supported.

Once you have installed 
`distribute <http://pypi.python.org/pypi/distribute>`_ or
`setuptools <http://pypi.python.org/pypi/setuptools>`_ you can install
RXPY with the command::

  easy_install rxpy

That's it.  There is no need to download anything beforehand;
``easy_install`` will do all the work.


Source
~~~~~~

A publicly readable Mercurial repository is `available
<http://code.google.com/p/rxpy/source/checkout>`_.
