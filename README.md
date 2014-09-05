gerrit-growler
==============

Receive a growl notification whenever your watched projects in Gerrit have
review activity.

Dependencies
------------

This currently depends on
[`terminal-notifier`](https://github.com/alloy/terminal-notifier) on OS X
10.8+ to produce notifications:

    $ brew install terminal-notifier

I'd be happy to see support added for additional notification frameworks.

Usage
-----

Just run the listener:

    $ python listen.py
