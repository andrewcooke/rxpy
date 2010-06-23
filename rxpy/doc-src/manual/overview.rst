
.. _overview:

Overview
========

There are three main components in RXPY:

* The parser, which constructs a graph that represents the regular
  expression.

* An engine, which evaluates the regular expression (expressed as a graph)
  against an input string, to find a match.

* An alphabet, which allows both the parser and engine to work with a variety
  of different input types.

So, for example, the expression ``(?P<number>[0-9]+)|\w*`` is compiled to the
graph shown (the entry point is not indicated, but would be ``...|...`` in
this case), but the interpretation of ``[0-9]`` and ``\w`` will depend on the
alphabet used (it will not be the same for ASCII and Unicode, for example).

.. figure::  example-graph.png
   :align:   center

