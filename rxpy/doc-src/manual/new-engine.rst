
Writing a New Engine
====================

I have tried to simplify as much as the possible the work need to develop a
new ``re`` package replacement.  If you want to implement a new matching
algorithm you should:

#. Sub-class `BaseEngine() <api/redirect.html#rxpy.engine.base.BaseEngine>`_ -
   this encapsulates the matching algorithm.

#. Use `Re() <api/redirect.html#rxpy.compat.module.Re>`_ to create the module
   contents (`example here <api/redirect.html#rxpy.engine.simple.re>`_).


An Example Engine
-----------------

RXPY includes a simple interpreter-based engine in the package
`rxpy.engine.simple <api/redirect.html#rxpy.engine.simple>`_.


Future Changes
--------------

RXPY is in active development and any aspect of the design may change.  The
general architecture is likely to be fairly stable, but new flags and opcodes
are inevitable.  Since there is currently only one engine, the engine related
API is an area that is unlikely to be sufficiently generic and, therefore,
particularly like to require adaptions.

At some point (once more engines exist), I hope to make the `rxpy.re` module
select the "best" engine for particular patterns.
