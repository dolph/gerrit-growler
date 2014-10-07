==============
gerrit-growler
==============

Receive a growl notifications from Gerrit.

Currently, you'll only receive notifications on reviews that you have starred.

Dependencies
------------

This currently depends on `terminal-notifier
<https://github.com/alloy/terminal-notifier>`_ on OS X 10.8+ to produce
notifications::

    $ brew install terminal-notifier

I'd be happy to see support added for additional notification frameworks.

Installation
------------

Install from PyPi::

    $ pip install gerrit-growler

Usage
-----

Just run the listener::

    $ gerrit-growler

See ``--help`` for authentication and Gerrit endpoint options.
