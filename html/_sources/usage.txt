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
``situp.py`` lets you define servers so you can interact with them by name
instead of URL: ::

	situp.py addserver -n dev -s http://localhost:5984

This creates a ``servers.json`` file in the current directory and stores the
server name, url and auth token in there. **DO NOT** make your ``servers.json``
file public since people will be able to access your couch instances.

Pushing to a (set of) servers
----------------------------------------
Pushing an application to a server is as simple as running: ::

	situp.py push -s http://localhost:5984 -d databasename

The -s option can be specified multiple times.

If a server has been defined (see above) you can refer to it via it's short
name: ::

	situp.py push -s dev -d databasename

If a server URL has a username in it (e.g. joe@localhost:5984) ``situp.py``
will ask for a password. This won't be stored anywhere and will not be in the
shell history.

You can have your applications javascript minified by specifiying the ``-m``
option with the push command.

Uploading documents (and attachments)
----------------------------------------
You might want to upload documents with ``situp.py``; because you are restoring
from backup or need to seed the database with some default documents. This is
managed via the push command, and assumes a certain structure for your
documents.

Any .json file in $APP_DIRECTORY/_docs will be uploaded when the ``situp.py
push`` command is executed. If you would like to attach files to those
documents create a directory with the same name as the file (minus the .json
extension) and put the files you want to attach in there.

For example, say I had a doc called ``foo.json`` and another called ``bar.json``
and I wanted to attach an image (``unicorn.png``) to ``foo.json``, I would need
to create a directory structure like: ::

	_docs
          \-------- foo.json
          +-------- foo
                    \--------unicorn.png
          +-------- bar.json

Fetching an app
----------------------------------------
You can pull a remote app into your current working directory by invoking: ::

	situp.py fetch http://foo.com/app_i_want

This will retrieve the app and all associated data.

Git hook
----------------------------------------

You can install a git post commit hook to push to your server at the same time
as committing to your git repository by running: ::

    situp.py githook
