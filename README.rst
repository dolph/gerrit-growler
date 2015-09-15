==============
gerrit-logger
==============

Log the Gerrit event stream in markdown.

This is a two-part tool which:

1. Captures the Gerrit event stream into a log file (using ``event-logger``).

2. Renders a log file of the Gerrit event stream into a human-readable markdown
   file (using ``events-in-english``).

Installation
------------

Clone the repository and install from source::

    $ pip install .

Usage
-----

Start by running the event logger::

    $ gerrit-logger

See ``--help`` for authentication and Gerrit endpoint options.

Next, you can (perhaps periodically) render a log file into markdown::

    $ cat event.log | gerrit-events-in-english
