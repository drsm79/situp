Using situp.py
========================================
Creating a view
----------------------------------------
::
    situp.py -d tst-app create view foo

Will create a view called foo in tst-app ($PWD/_design/tst-app) with empty map
and reduce files.

::
    situp.py -d tst-app create view bar --sum

Will create a view called bar in tst-app ($PWD/_design/tst-app) with an empty
map.js and a _sum built in reduce.

::
    situp.py create view baz

Will create the view baz in the views directory of the current working dir
(e.g. $PWD/views/baz)


Importing a vendor
----------------------------------------
::
    situp.py -d tst-app vendor backbone

Will download and install the vendor backbone and its dependencies into the
tst-app design.

Pushing to a set of servers
----------------------------------------
::
    situp.py -d tst-app push -s http://localhost:5984 -d databasename

The -s option can be specified multiple times.
