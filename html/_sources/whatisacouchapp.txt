About situp.py
----------------------------------------

``situp.py`` originally started out as an attempt to write a simplified
CouchApp "client" that followed and reused the python distutils package, the
idea being that distutils would take care of lots of the heavy lifting (and
provide a few features "out of the box"). After a bit of tinkering it became
fairly apparent that a lot of code would be necessary to override distutils
behaviour. So now ``situp.py`` is just another CouchApp client (and an excuse
to experiment with a few things).

A key feature of ``situp.py`` is that it's only dependency is python - this
makes it easy to use in automated test/install situations. If you don't want to
use minification it's a single file.


What is a CouchApp?
----------------------------------------

My colleague Mike can probably `tell you better <https://github.com/mikewallace1979/CouchApp-Handbook>`_
than I! In short a couchapp is an application that serves and is served from
Apache CouchDB.
