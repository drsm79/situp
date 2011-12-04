import base64
import json
import httplib
import os
import sys
import logging
import urllib
import urllib2
import tarfile
import zipfile
import shutil
import uuid
import mimetypes
import getpass
from optparse import OptionParser, OptionGroup
from collections import defaultdict, namedtuple
from urlparse import urlunparse, urlparse
from httplib import HTTPConnection
from httplib import HTTPSConnection
from httplib import HTTPException

__version__ = 0.1

class Command:
    """
    A command has a name, an option parser and a dictionary of sub commands it
    can call.
    """
    command_name = "interface"
    no_required_args = 0
    required_opts = []
    dependencies = []
    usage = "usage: %prog [options] COMMAND [options] [args]"

    def __init__(self):
        """
        Initialise the logger and OptionParser for the Command.
        """
        logging.basicConfig()
        self.logger = logging.getLogger('situp-%s' % self.command_name)
        self.logger.setLevel(logging.DEBUG)

        self.sub_commands = {}
        # Need to deal with competing OptionParsers...
        self.parser = OptionParser()
        self.parser.disable_interspersed_args()
        self.register_sub_commands()
        self.parser.set_usage(self.usage)

        self.parser.epilog = " ".join(str(self.__doc__).split())
        self._add_options()

    def __call__(self, args=None, options=None):
        """
        Set up the logger, work out if I should print help or call the command.
        """
        (options, args) = self.process_args(args, options)
        self.configure_logger(options)

        self.logger.debug('called')
        self.logger.debug(args)
        self.logger.debug(options)

        if options.cmd_help:
            # call the print_help function for the command and exit
            if len(args) and args[0] in self.sub_commands.keys():
                self.sub_commands[args[0]].print_help(args)
            else:
                self.exit_invalid("You must specify a valid action for --cmd-help.")
        elif options.version:
            print "situp.py version %s" % __version__
            sys.exit(0)
        if len(args) and len(self.sub_commands.keys()) and \
                                    args[0] not in self.sub_commands.keys():
            self.exit_invalid("You must specify a valid command.")
        self.run_command(args, options)

    def run_command(self, args=None, options=None):
        self.sub_commands[args[0]](args[1:], options)

    def process_args(self, args=None, options=None):
        """
        Process the option parser, updating it with data from parent parser
        then check the args are valid.
        """
        if options:
            (new_options, args) = self.parser.parse_args(args=args)#, values=options)
            options._update(new_options.__dict__, 'loose')
        elif args:
            (options, args) = self.parser.parse_args(args=args)
        else:
            (options, args) = self.parser.parse_args()

        die = False
        for option in self.required_opts:
            if options.ensure_value(option, 'NOTSET') == 'NOTSET':
                print '%s is a required option and not set' % option
                die = True
        if die:
            print 'Run command with -h/--help for further information'
            sys.exit(1)
        return options, args

    def configure_logger(self, options):
        if options.quiet:
            self.logger.setLevel(logging.WARNING)
        if options.silent:
            self.logger.setLevel(logging.CRITICAL)
        elif options.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def _add_options(self):
        """
        Add options to the command's option parser
        """
        group = OptionGroup(self.parser, "Base options", "")

        group.add_option("--quiet",
                    action="store_true", dest="quiet", default=False,
                    help="reduce messages going to stdout")

        group.add_option("--debug",
                    action="store_true", dest="debug", default=False,
                    help="print extra messages to stdout")

        group.add_option("--silent",
                    action="store_true", dest="silent", default=False,
                    help="print no messages to stdout")

        group.add_option("--version",
                    action="store_true", dest="version", default=False,
                    help="print situp.py version and exit")

        group.add_option("--cmd-help",
                    metavar="COMMAND",
                    dest="cmd_help",
                    action="store_true",default=False,
                    help="print help for the named command")

        self.parser.add_option_group(group)

    def register_sub_commands(self):
        """
        This is a dummy method for subclasses to fill in
        """
        pass

    def _register(self, commands, usage=False):
        """
        Initialise subcommand classes for the command and update the optparser
        """
        for cmd in commands:
            self.sub_commands[cmd.command_name] = cmd
        if not usage:
            self.usage = "usage: %prog " + self.command_name
            self.usage += " [%s]" %  '|'.join(self.sub_commands.keys())
            self.usage += " [options] [args]"

    def print_help(self, args):
        """
        Encapsulate the Command's option parser's print_help() method here in
        case there's some reason to override it.

        parser.print_help() actually prints to the screen, so just run that.
        """

        if len(args) > 1 and args[1] in self.sub_commands.keys():
            self.sub_commands[args[1]].print_help(args[2:])
        self.parser.print_help()
        sys.exit(0)

    def exit_invalid(self, msg):
        """
        The command doesn't exist so bail
        """
        print msg
        # Described the valid commands in epilog, reuse here
        print self.parser.epilog
        sys.exit(-1)

class SitUp(Command):
    """
    The main user interface command.
    """
    def _add_options(self):
        commands = sorted(self.sub_commands.keys())
        self.parser.epilog = "Valid commands are: %s" % ", ".join(commands)

        # This is the important bit
        group = OptionGroup(self.parser, "Situp options", "Situp allows you to"
                    " have multiple design documents in your application via"
                    " the -d/--design switch. You can work on your app in"
                    " another directory by specifying -r/--root"
        )
        group.add_option("-d", "--design",
                    metavar="DESIGN",
                    dest="design",
                    default=['_design'],
                    action='append',
                    help="modify the design document DESIGN")

        pwd = os.getcwd()
        group.add_option("-r", "--root",
                    dest="root", default=pwd,
                    help="Application root directory, default is %s" % pwd)

        self.parser.add_option_group(group)
        Command._add_options(self)

    def register_sub_commands(self):
        """
        Register my commands
        """
        sub_commands = [Create(), InstallVendor(), Push(), Fetch(), AddServer()]
        self._register(sub_commands)

LocatedFile = namedtuple('LocatedFile', ['path', 'filename'])

class AddServer(Command):
    """
    Add a server to the servers.json file
    """
    command_name = 'addserver'
    required_opts = ['name', 'server']

    def _add_options(self):
        """
        Give the OptionParser additional options
        """
        self.parser.add_option("-s", "--server",
                dest="server",
                help="The server to add [required]")
        self.parser.add_option("-n", "--name",
                dest="name",
                help="The simple name server to add [required]")
        #self.parser.add_option("--noauth",
        #        dest="servers", default=[], action='append',
        #        help="Push the app to one or more servers (multiple -s options are allowed)")
        Command._add_options(self)

    def process_args(self, args=None, options=None):
        options, args = Command.process_args(self, args, options)
        username = raw_input('Username for server, press enter for no user/password auth:')
        if username:
            options.auth_string = "%s" % base64.encodestring('%s:%s' % (
                                           username, getpass.getpass())).strip()
        return options, args

    def run_command(self, args, options):
        servers = {}
        if os.path.exists('servers.json'):
            f = open('servers.json')
            servers = json.load(f)
            f.close()
        servers[options.name] = {'url':options.server}
        if options.ensure_value('auth_string', False):
            servers[options.name]['auth'] = options.auth_string
        f = open('servers.json', 'w')
        json.dump(servers, f)
        f.close()

class Push(Command):
    """
    The Push command sends the application to the CouchDB server. Specify a
    design to push only a single design document, otherwise all designs in the
    app will be pushed.
    """
    command_name = 'push'
    no_required_args = 0
    #TODO pick this up from config
    #TODO support regexp
    ignored_files = ['.DS_Store', '.cvs', '.svn', '.hg', '.git']

    def _add_options(self):
        """
        Give the OptionParser additional options
        """
        #Create commands can add the created documents to an index
        self.parser.add_option("-o", "--open",
                dest="open_app",
                action="store_true", default=False,
                help="Once pushed, open the application")
        self.parser.add_option("-s", "--server",
                dest="servers", default=[], action='append',
                help="Push the app to one or more servers (multiple -s options are allowed)")
        self.parser.add_option('-d', '--database', dest='database',
                help='the database to write to.')
        Command._add_options(self)

    def _push_docs(self, docs_list, db, servers):
        """
        Push dictionaries into json docs in the server
        TODO: spin off into a worker thread
        """
        for server in servers.keys():
            srv = servers[server]
            print 'upload to %s (%s/%s)' % (server, srv['url'], db)
            try:
                def request(server, method, url, auth=False):
                    conn = None
                    if server.startswith('https://'):
                        conn = httplib.HTTPSConnection(server.strip('https://'))
                    else:
                        conn = httplib.HTTPConnection(server.strip('http://'))
                    if auth:
                        conn.request(method, url, headers={"Authorization": "Basic %s" % auth})
                    else:
                        conn.request(method, url)
                    response = conn.getresponse()
                    conn.close()
                    return response

                request(srv['url'], 'PUT', "/%s" % db, srv.get('auth', False))

                for doc in docs_list:
                    docid = doc['_id']
                    # HEAD the doc
                    head = request(srv['url'], 'HEAD', "/%s/%s" % (db, docid), srv.get('auth', False))
                    # get its _rev, append _rev to the doc dict
                    if head.getheader('etag', False):
                        doc['_rev'] = head.getheader('etag', False).replace('"', '')

                req = urllib2.Request('%s/%s/_bulk_docs' % (srv['url'], db))
                req.add_header("Content-Type", "application/json")
                if 'auth' in srv.keys():
                    req.add_header("Authorization", "Basic %s" % srv['auth'])
                data = {'docs': docs_list}
                req.add_data(json.dumps(data))
                f = urllib2.urlopen(req)
                print f.read()
            except Exception, e:
                print "upload to %s failed" % server
                print e

    def _walk_design(self, name, design):
        """
        Walk through the design document, building a dictionary as it goes.
        """


        def nest(path_dict, path_elem):
            """
            Build the required nested data structure
            """
            if path_elem not in self.ignored_files:
                return {path_elem: path_dict}

        def recursive_update(a_dict, b_dict):
            for k, v in b_dict.items():
                if k not in a_dict.keys() or type(v) != type(a_dict[k]):
                    a_dict[k] = v
                else:
                    a_dict[k] = recursive_update(a_dict[k], v)
            return a_dict

        attachments = {}
        app = {'_id': name}
        for root, dirs, files in os.walk(design):
            path = root.split(name)[1].split('/')[1:]
            for walkeddir in dirs:
                if walkeddir in self.ignored_files:
                    print 'ignoring %s' % os.path.join(root, walkeddir)
                    dirs.remove(walkeddir)
            if files:
                d = {}
                for afile in files:
                    if afile in self.ignored_files:
                        print 'ignoring %s' % afile
                        continue
                    if '_attachments' in path:
                        tmp_path = list(path) # avoid overwriting the original path var
                        tmp_path.remove('_attachments')
                        tmp_path.append(afile)
                        attachments['/'.join(tmp_path)] = {
                            'data': base64.encodestring(open(os.path.join(root, afile)).read()),
                            'content_type': mimetypes.guess_type(os.path.join(root, afile))[0]
                        }
                    else:
                        if len(path) > 0 and path[0] == 'views':
                            if afile in ['map.js', 'reduce.js']:
                                d[afile.strip('.js')] = open(os.path.join(root, afile)).read()
                        else:
                            d[afile] = open(os.path.join(root, afile)).read()
                if d.keys():
                    app = recursive_update(app, reduce(nest, reversed(path), d))

        if attachments:
            app['_attachments'] = attachments

        return app

    def _process_url(self, url):
        """ Extract auth credentials from url, if present """
        parts = urlparse(url)
        if not parts.username and not parts.password:
            return url, None
        netloc = '%s:%s' % (parts.hostname, parts.port)
        url = urlunparse((parts.scheme, netloc, parts.path, parts.params, parts.query, parts.fragment))
        if parts.username and parts.password:
            return url, "%s" % base64.encodestring('%s:%s' % (parts.username, parts.password)).strip()
        else:
            return url, "%s" % base64.encodestring('%s:%s' % (
                                           parts.username, getpass.getpass())).strip()

    def run_command(self, args, options):
        """
        Build a python dictionary of the application, jsonise it and push it to
        CouchDB
        """
        print "Running Push Command for application in %s" % options.root

        docs = os.path.join(options.root, '_docs')
        designs = os.path.join(options.root, '_design')
        apps_to_push = []
        attachments_to_push = []

        saved_servers = {}
        servers_to_use = {}
        if os.path.exists('servers.json'):
            saved_servers = json.load(open('servers.json'))

            for server in options.servers:
                if server in saved_servers.keys():
                    servers_to_use[server] = saved_servers[server]
                else:
                    url, auth = self._process_url(server)
                    servers_to_use[server] = {"url": url}
                    if auth:
                        servers_to_use[server]["auth"] = auth

        # TODO: push docs here too.
        if os.path.exists(designs):
            list_of_designs = os.listdir(designs)
            if len(options.design) > 1:
                list_of_designs = [options.design[1]]
            for design in list_of_designs:
                if design not in self.ignored_files:
                    name = os.path.join('_design', design)
                    root = os.path.join(designs, design)
                    app = self._walk_design(name,root)
                    apps_to_push.append(app)

		self._push_docs(apps_to_push, options.database, servers_to_use)

		if os.path.exists('_docs'):
			docs_to_push = []
			for jsonfile in docs:
				# do something to check it's json
				f = open('_docs/%s' % jsonfile)
				docs_to_push.append(json.load(f))
				f.close()
			self._push_docs(docs_to_push, options.database, servers_to_use)

class Fetch(Command):
    """
    Copy a remote CouchApp into the working directory.
    """
    command_name = 'fetch'

class Create(Command):
    """
    Create a component of a CouchApp. See View(), ListGen(), Show(), Design(),
    App() and Document()
    """
    command_name = "create"
    no_required_args = 2

    def _add_options(self):
        """
        Give the OptionParser additional options
        """
        #Create commands can add the created documents to an index
        self.parser.add_option("--index",
                dest="index",
                action="store_true", default=False,
                help="Add created document to an index")

        Command._add_options(self)
        commands = sorted(self.sub_commands.keys())
        self.parser.epilog = "Valid entities are: %s" % ", ".join(commands)

    def register_sub_commands(self):
        """
        Set up the sub_commands and the OptionParser.
        """
        self._register([ View(), ListGen(), Show(), Design(), App(), Document(), Html() ])

        commands = sorted(self.sub_commands.keys())
        self.parser.epilog = "Valid entities are: %s" % ", ".join(commands)

class InstallVendor(Command):
    """
    Command to install a vendor from a remote source.
    """
    command_name = "vendor"
    no_required_args = 1

    def _add_options(self):
        group = OptionGroup(self.parser, "Vendor options",
                            "You can install vendors from non-standard "
                            "locations by specifying the URL on the command"
                            " line")

        externals = {}
        for vendor in self.sub_commands.values():
            externals.update(vendor._template)
        for external, package in externals.items():
            group.add_option("--%s" % external, metavar="URL",
                        dest="alt_%s" % external, default=False,
                        help="Download %s from URL instead of the default [%s]"\
                            % (external, package.url))
        self.parser.add_option_group(group)

        commands = sorted(self.sub_commands.keys())
        self.parser.epilog = "Valid vendors are: %s" % ", ".join(commands)

    def register_sub_commands(self):
        """
        Set up the sub_commands and the OptionParser.
        """
        self._register([ Backbone(), d3(), BackboneCouchDB() ])

class Generator(Command):
    """
    A generator knows how to create files and where to create them.
    """
    # _template is a dict of filename:it's content
    _template = {}
    # the type of thing the generator generates
    command_name = "generator_interface"
    path_elem = None
    def __init__(self):
        self.usage = "usage: %prog create " + self.command_name + " [options] [args]"
        Command.__init__(self)

    def run_command(self, args, options):
        """
        Run the generator
        """
        #self.process_args(args, options)
        path = None
        if len(args):
            path = self._create_path(options.root, options.design, args[0])
        else:
            path = self._create_path(options.root, options.design)
        self._push_template(path, args, options)

    def _create_path(self, root, design=[], name=None, misc=None):
        """
        Create the path the generator needs
        """
        if os.path.exists(root):
            path_elems =[root]
            if len(design) > 1:
                path_elems.extend(design)

            if name:
                if not self.path_elem:
                    self.path_elem = self.command_name
            path_elems.extend([self.path_elem, name])

            if misc:
                path_elems.extend(misc)

            path_elems = [item for item in path_elems if item != None]
            path = os.path.join(*tuple(path_elems))
            self.logger.debug('Creating: %s' % path)
            if not os.path.exists(path):
                os.makedirs(path)
            return path
        else:
            raise OSError('Application directory (%s) does not exist' % root)

    def _write_file(self, path, content):
        """
        Write content to a file.
        """
        f = open(path, 'w')
        f.write(content)
        f.write('\n')
        f.close()

    def _write_json(self, path, obj):
        """
        Write an object to json
        """
        f = open(path, 'w')
        json.dump(obj, f)
        f.close()

    def _push_template(self, path, args, options):
        """
        Create files following _templates
        """
        raise NotImplementedError

class View(Generator):
    """
    Create the map.js and reduce.js files for a view. Can use built in erlang
    reducers (faster) for the reduce.js (see options above).
    """
    command_name = "view"
    path_elem = "views"
    _template = {
        'map.js': '''function(doc){
  emit(null, 1)
}''',
        'reduce.js': '''function(key, values, rereduce){

}''',
    }

    def _add_options(self):
        """
        Allow for using a built in reduce.
        """
        self.parser.add_option("--builtin-reduce",
                            dest="built_in", default=False,
                            choices=['sum', 'count', 'stats'],
                            help="Use a built in reduce (one of sum, count, stats)")

        for reducer in ['sum', 'count', 'stats']:
            self.parser.add_option("--%s" % reducer,
                    dest="built_in", default=False,
                    action="store_const", const=reducer,
                    help="Use the %s built in reduce, shorthand for --builtin-reduce=%s" % (reducer, reducer)
                    )

    def _push_template(self, path, args, options):
        """
        Create files following _templates, built_in should be either unset
        (False) or be the name of a built in reduce function.
        """
        reduce_file = os.path.join(path, 'reduce.js')
        map_file = os.path.join(path, 'map.js')
        self._write_file(map_file, self._template['map.js'])
        if options.built_in:
            self._write_file(reduce_file, '_%s' % options.built_in)
        else:
            self._write_file(reduce_file, self._template['reduce.js'])

class ListGen(Generator):
    command_name = "list"

class Show(Generator):
    command_name = "show"

class Filter(Generator):
    command_name = "filter"

class Design(Generator):
    command_name = "design"

class App(Generator):
    command_name = "app"

class Document(Generator):
    """
    Create an empty json document (containing just an _id) in the _docs folder
    of the application root.
    """
    command_name = 'document'
    path_elem = '_docs'
    _template = {'document': {}}

    def _add_options(self):
        self.parser.add_option("--name",
                    dest="name",
                    help="Name the document")

    def _push_template(self, path, args, options):
        path = self._create_path(options.root)
        file_name = str(uuid.uuid1())
        doc = self._template['document']
        doc['_id'] = file_name
        if options.ensure_value('name', False):
            doc['_id'] = options.name
            file_name = options.name
        doc_file = os.path.join(path, file_name)

        self._write_json(doc_file, doc)

class Html(Document):
    """
    Create an empty html document in the _attachments folder of the specified
    design document.
    TODO: include script tags for all vendors in generated html.
    """
    command_name = 'html'
    path_elem = '_attachments'
    _template = {
        'document': '<html><head><title>REPLACE</title></head><body><h1>REPLACE</h1></body></html>'
    }
    required_opts = ['name']

    def _add_options(self):
        self.parser.add_option("--name",
                    dest="name", help="Name the document")

    def _push_template(self, path, args, options):
        file_name = '%s.html' % options.name.replace('html', '')

        doc = self._template['document'].replace('REPLACE', options.name.title())
        doc_file = os.path.join(path, file_name)

        self._write_file(doc_file, doc)

def fetch_archive(url, path, filter_list=[]):
    """
    Fetch a remote tar/zip archive and extract it, applying a filter if one is provided.
    """
    (filename, response) = urllib.urlretrieve(url)
    subfolder = ""
    if tarfile.is_tarfile(filename):
        tgz = tarfile.open(filename)
        to_extract = tgz.getmembers()
        subfolder = to_extract[0].name
        if filter_list:
            #lambda f: f.name in filter_list
            def filter_this(f):
                return filter(lambda g: f.name.endswith(g), filter_list)
            for member in filter(filter_this, to_extract):
                tgz.extract(member, path)
        else:
            tgz.extractall(path)
        tgz.close()
    elif zipfile.is_zipfile(filename):
        myzip = zipfile.ZipFile(filename)
        to_extract = myzip.infolist()
        subfolder = to_extract[0].filename
        if filter_list:
            def filter_this(f):
                return filter(lambda g: f.filename.endswith(g), filter_list)
            for member in filter(filter_this, to_extract):
                myzip.extract(member, path)
        else:
            myzip.extractall(os.path.join(path, '_attachments'))
        myzip.close()
    else:
        print 'ERROR: %s is not a readable archive' % url
        sys.exit(-1)
    # TODO: use a --force option
    try:
        shutil.rmtree(os.path.join(path, '_attachments'))
    except:
        pass
    dest = os.path.join(path, '_attachments/')
    os.mkdir(dest)
    for sfile in os.listdir(os.path.join(path, subfolder)):
        source = os.path.join(path, subfolder, sfile)
        shutil.move(source, dest) #, sfile
        #copyfile
    shutil.rmtree(os.path.join(path, subfolder))
    os.remove(filename)

Package = namedtuple('Package', ['url', 'filter'])

class Vendor(Generator):
    """
    Vendors are generators that download external code into the right place

    TODO: run make/build commands as needed
    """
    command_name = "vendor"
    def run_command(self, args, options):
        """
        Vendors behave differently to other generators
        """
        self.logger.warning("Fetching externals, may take a while")
        # bit of a hack...
        self.command_name = ""
        for external, package in self._template.items():
            path = self._create_path(options.root,
                                    options.design,
                                    'vendor/%s' % external)
            self.logger.debug('Installing %s into %s' % (external, path))
            self.logger.debug('Fetching %s from %s' % (external, package.url))
            fetch_archive(package.url, path, filter_list=package.filter)
            self.logger.info("Installed %s to %s" % (external, path))

class Backbone(Vendor):
    """
    Install Backbone Couch
    """
    command_name = 'backbone'
    _template = {
        'backbone' : Package('https://github.com/documentcloud/backbone/zipball/master', ['backbone.js']),
        'backbone.couch' : Package('https://github.com/drsm79/backbone-couch/tarball/master', ['backbone.couch.js']),
        'underscore' : Package('https://github.com/documentcloud/underscore/tarball/master', ['underscore-min.js'])
    }

class BackboneCouchDB(Vendor):
    """
    Install Backbone CouchDB
    """
    command_name = 'backbonecouchdb'
    _template = {
        'backbone' : Package('https://github.com/documentcloud/backbone/zipball/master', ['backbone.js']),
        'backbonecouchdb' : Package('https://github.com/janmonschke/backbone-couchdb/tarball/master', ['backbone-couchdb.js']),
        'underscore' : Package('https://github.com/documentcloud/underscore/tarball/master', ['underscore-min.js'])
    }


class YUI(Vendor):
    """
    Install YUI
    """
    command_name = 'yui'
    _template = {}

class d3(Vendor):
    """
    Install d3
    """
    command_name = 'd3'
    _template = {
        'd3' : Package('https://github.com/mbostock/d3/tarball/v2.4.4', ['min.js']),
    }

if __name__ == "__main__":
    situp = SitUp()
    situp()
