Using situp.py
========================================
Creating a view
----------------------------------------
situp.py will create a view called foo in tst-app ($PWD/_design/tst-app) with
empty functions in the map.js and reduce.js files.::

	situp.py -d tst-app create view foo

Will create a view called bar in tst-app ($PWD/_design/tst-app) with an empty
function in map.js and a _sum built in reduce.::

	situp.py -d tst-app create view bar --sum

Will create the view baz in the views directory of the current working dir
(e.g. $PWD/views/baz)::

	situp.py create view baz


Importing a vendor
----------------------------------------
Vendors can be imported into the application via: ::

	situp.py -d tst-app vendor backbone

Will download and install the vendor backbone and its dependencies into the
tst-app design. Supported vendors are:

* Backbone (both flavours)
* d3
* YUI (soon...)

Adding a vendor to situp.py should be simple, for instance the d3 vendor looks like ::

	class d3(Vendor):
    	"""
	    Install d3
	    """
	    command_name = 'd3'
	    _template = {
	        'd3' : Package('https://github.com/mbostock/d3/tarball/v2.4.4', ['min.js']),
	    }

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

	situp.py -d tst-app push -s http://localhost:5984 -d databasename

The -s option can be specified multiple times.

If a server has been defined (see above) you can refer to it via it's short
name: ::

	situp.py -d tst-app push -s dev -d databasename

If a server URL has a username in it (e.g. joe@localhost:5984) situp.py will
ask for a password. This won't be stored anywhere and will not be in the shell
history.