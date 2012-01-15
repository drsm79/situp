Using situp.py
========================================
Help
----------------------------------------
All commands in situp.py have a help function. Invoke it by running: ::

    setup.py <command> -h


Multiple design doc support
----------------------------------------
situp.py supports couchapps that use multiple design documents. If you just
want the current directory to be your application just run situp.py as: ::

	situp.py view foo

If you would like to create a view in a specific design doc, run the command
as: ::

	situp.py view foo -d tst-app

Creating views, lists, shows and filters
----------------------------------------
situp.py will create a view called foo in tst-app ($PWD/_design/tst-app) with
empty functions in the map.js and reduce.js files.::

	situp.py view foo

Will create a view called bar in tst-app ($PWD/_design/tst-app) with an empty
function in map.js and a _sum built in reduce.::

	situp.py view bar --sum

Will create the view baz in the views directory of the current working dir
(e.g. $PWD/views/baz)::

	situp.py view baz

The same syntax will create lists, shows and filters: ::

	situp.py list mylist
	situp.py show myshow
	situp.py filter myfilter

Importing a vendor
----------------------------------------
Vendors can be imported into the application via: ::

	situp.py vendor <vendor-name>

Will download and install the vendor backbone and its dependencies into the
tst-app design. situp.py uses the kanso packages, so anything that is available
on http://kan.so/packages/ should work with situp.

Defining servers
----------------------------------------
situp.py lets you define servers so you can interact with them by name instead
of URL: ::

	situp.py addserver -n dev -s http://localhost:5984

This creates a servers.json file in the current directory and stores the server
name, url and auth token in there. **DO NOT** make your servers.json file public
since people will be able to access your couch instances.

Pushing to a (set of) servers
----------------------------------------
Pushing an application to a server is as simple as running: ::

	situp.py push -s http://localhost:5984 -d databasename

The -s option can be specified multiple times.

If a server has been defined (see above) you can refer to it via it's short
name: ::

	situp.py push -s dev -d databasename

If a server URL has a username in it (e.g. joe@localhost:5984) situp.py will
ask for a password. This won't be stored anywhere and will not be in the shell
history.

Git hook
----------------------------------------

You can install a git post commit hook to push to your server at the same time
as committing to your git repository by running: ::

    situp.py githook
