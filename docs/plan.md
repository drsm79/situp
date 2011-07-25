situp.py
========================================
General features
----------------------------------------
Reuse setup.py/distills for couch apps
 * Build command creates json docs and tar ball of the app
 * Install command pushes it to server

Password protection - ask or read from file
NO externals, use plain python, support py3?
Markdown compile if markdown installed on upload of _attachments http://daringfireball.net/projects/markdown/
Better support of BigCouch
situp.py location aware. If not in an app directory only allows generate app command, copies itself into that app.

Minimal generate:
----------------------------------------
	-g/--generate {app, design, view, list, show, update, filter...} name
 * Generator base class for all generate options
 * View generator takes optional reduce - use a builtin reduce instead of making a js function
 * index option adds the generated thing to an index file

Extensible plugin/vendor support
----------------------------------------
 * Backbone
 * YUI
 * evently
	-i/--install to bring in plugins
	--github pull in code from github

Directory structure
----------------------------------------
 * design
  * Similar to now
 * docs
  * Documents to push, also mapped to file/directory structure
 * settings.json - server URL, user/pass etc

Additional Options
----------------------------------------
	--clean delete database
	--check prompt to create database
	-b/--browse open app in browser
