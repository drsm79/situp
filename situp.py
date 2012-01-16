#! /usr/bin/env python
import base64
import json
import httplib
import os
import sys
import stat
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

CAN_MINIFY_JS = False

try:
    from minify import jsmin
    CAN_MINIFY_JS = True
except:
    pass

__version__ = "0.1.2"

class CommandDispatch:
    def __init__(self):
        self.commands = {}
        self.default = ''

    def register_command(self, command, default = False):
        self.commands[command.name.lower()] = command
        if default: self.default = command.name.lower()

    def __call__(self, command = False):
        if command:
            self.commands[command]()
        else:
            self.default_command()

    def default_command(self):
        if self.default:
            self.commands[self.default]()
        else:
            usage = '%prog command [options]\n'
            usage += 'Available commands: '
            usage += ' '.join(sorted(self.commands.keys()))
            self.parser = OptionParser(usage=usage, version=__version__)
            self.parser.parse_args()
            self.parser.print_help()

class Command:
    """
    A command has a name, an option parser and a dictionary of sub commands it
    can call.
    """
    name = "interface"
    no_required_args = 0
    required_opts = []
    dependencies = []
    usage = "usage: %prog [options] COMMAND [options] [args]"

    def __init__(self):
        """
        Initialise the logger and OptionParser for the Command.
        """
        logging.basicConfig()
        self.logger = logging.getLogger('situp-%s' % self.name)
        self.logger.setLevel(logging.DEBUG)

        # Need to deal with competing OptionParsers...
        self.parser = OptionParser(conflict_handler="resolve")
        self.parser.set_usage(self.usage)

        self.parser.epilog = " ".join(str(self.__doc__).split())
        self._default_options()
        self._add_options()

    def __call__(self):
        """
        Set up the logger, work out if I should print help or call the command.
        """
        (options, args) = self._process_args()

        self._configure_logger(options)

        self.logger.debug('called')
        self.logger.debug(args)
        self.logger.debug(options)

        self.run_command(args, options)

    def run_command(self, args=None, options=None):
        raise NotImplementedError('Not implemented in base class')

    def _process_args(self):
        """
        Process the option parser, updating it with data from parent parser
        then check the args are valid.
        """
        (options, args) = self.parser.parse_args()

        die = False
        for option in self.required_opts:
            if options.ensure_value(option, 'NOTSET') == 'NOTSET':
                print '%s is a required option and not set' % option
                die = True
        if die:
            print 'Run command with -h/--help for further information'
            sys.exit(1)
        return options, args[1:]

    def _configure_logger(self, options):
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
        pass


    def _default_options(self):
        group = OptionGroup(self.parser, "Base options", "")

        group.add_option("--quiet",
                action="store_true", dest="quiet", default=False,
                help="reduce messages going to stdout")

        group.add_option("--debug",
                action="store_true", dest="debug", default=False,
                help="print extra messages to stdout")

        group.add_option("--version",
                action="store_true", dest="version", default=False,
                help="print situp.py version and exit")

        group.add_option("--silent",
                action="store_true", dest="silent", default=False,
                help="print as little as possible to stdout")

        self.parser.add_option_group(group)

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

LocatedFile = namedtuple('LocatedFile', ['path', 'filename'])

class AddServer(Command):
    """
    Add a server to the servers.json file
    """
    name = 'addserver'
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
    name = 'push'
    no_required_args = 0
    #TODO: pick this up from config
    #TODO: support regexp
    ignored_files = ['.DS_Store', '.cvs', '.svn', '.hg', '.git']

    def _add_options(self):
        """
        Give the OptionParser additional options
        """
        about =  "Options available to the push command."
        group = OptionGroup(self.parser, "Push options", about)
        group.add_option("-o", "--open",
                dest="open_app",
                action="store_true", default=False,
                help="Once pushed, open the application")
        group.add_option("-s", "--server",
                dest="servers", default=[], action='append',
                help="Push the app to one or more servers (multiple -s options are allowed)")
        group.add_option('-d', '--database', dest='database',
                help="Push the app to named database")
        if CAN_MINIFY_JS:
            group.add_option("-m", "--minify",
                dest="minify", default=False, action="store_true",
                help="Minify javascript before pushing to database")


        self.parser.add_option_group(group)

    def _push_docs(self, docs_list, db, servers):
        """
        Push dictionaries into json docs in the server
        TODO: spin off into a worker thread
        """
        for server in servers.keys():
            srv = servers[server]
            self.logger.info('upload to %s (%s/%s)' % (server, srv['url'], db))
            data = {}
            try:
                def request(server, method, url, auth=False):
                    conn = None
                    if server.startswith('https://'):
                        conn = httplib.HTTPSConnection(server.strip('https://'))
                    else:
                        conn = httplib.HTTPConnection(server.strip('http://'))
                    if auth:
                        conn.putrequest(method, url,
                                headers={"Authorization": "Basic %s" % auth})
                    else:
                        conn.putrequest(method, url)
                    conn.putheader("User-Agent", "situp-%s" % __version__)
                    conn.endheaders()
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
                req.add_header("User-Agent", "situp-%s" % __version__)
                if 'auth' in srv.keys():
                    req.add_header("Authorization", "Basic %s" % srv['auth'])
                data = {'docs': docs_list}
                req.add_data(json.dumps(data))
                f = urllib2.urlopen(req)
                self.logger.info(f.read())
            except Exception, e:
                self.logger.error("upload to %s failed" % server)
                self.logger.info(e)


    def _walk_design(self, name, design, options):
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
                    self.logger.debug('ignoring %s' % os.path.join(root,
                        walkeddir))
                    dirs.remove(walkeddir)
            if files:
                d = {}
                for afile in files:
                    if afile in self.ignored_files:
                        self.logger.debug('ignoring %s' % afile)
                        continue
                    if '_attachments' in path:
                        tmp_path = list(path) # avoid overwriting the original path var
                        tmp_path.remove('_attachments')
                        tmp_path.append(afile)

                        mime = mimetypes.guess_type(os.path.join(root, afile))[0]

                        if not mime:
                            msg = 'Assuming text/plain mime type for %s'
                            self.logger.warning(msg % afile)
                            mime = 'text/plain'

                        if options.minify and mime == "application/javascript":
                            try:
                                mini = jsmin(open(os.path.join(root, afile)).read())
                                data = base64.encodestring(mini)
                            except:
                                self.logger.debug("Could not minify %s, uploading expanded version" % afile)
                                data = base64.encodestring(open(os.path.join(root, afile)).read())
                        else:
                            data = base64.encodestring(open(os.path.join(root, afile)).read())

                        attachments['/'.join(tmp_path)] = {
                            'data': data,
                            'content_type': mime
                        }
                    else:
                        if len(path) > 0 and path[0] in ['views', 'lists',
                                'shows', 'filters']:
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
        self.logger.debug("Running Push Command for application in %s" %
                options.root)

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
                    app = self._walk_design(name, root, options)
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
    name = 'fetch'


class InstallVendor(Command):
    """
    Command to install a vendor from a remote source.
    """
    name = "vendor"
    no_required_args = 1

    def _add_options(self):
        group = OptionGroup(self.parser, "Vendor options", "")

        group.add_option("--ext_version",
          default='latest', dest="ext_version",
          help="Install a specific version of the external, default is latest")

        self.parser.add_option_group(group)


    def run_command(self, args, options):
        """
        """
        vendor = FetchVendors()
        vendor(args, options)

class Generator(Command):
    """
    A generator knows how to create files and where to create them.
    """
    # _template is a dict of filename:it's content
    _template = {}
    # the type of thing the generator generates
    name = "generator_interface"
    path_elem = None
    def __init__(self):
        self.usage = "usage: %prog " + self.name + " [options] [args]"
        Command.__init__(self)

    def run_command(self, args, options):
        """
        Run the generator
        """
        #self.process_args(args, options)
        path = None
        if self.name == "view" and len(args):
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
                    self.path_elem = self.name
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
        path = os.path.join(path, '%s.js' % args[0].replace('.js', ''))
        self._write_file(path, self._template[self.name])


class View(Generator):
    """
    Create the map.js and reduce.js files for a view. Can use built in erlang
    reducers (faster) for the reduce.js (see options above).
    """
    name = "view"
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
    name = "list"
    path_elem = "lists"
    _template = {'list': '''function(doc, req) {

}'''}

class Show(Generator):
    name = "show"
    path_elem = "shows"
    _template = {'show': '''function(doc, req) {

}'''}


class Filter(Generator):
    name = "filter"
    path_elem = "filters"
    _template = {'filter': '''function(doc, req) {
  return true;
}'''}

class Update(Generator):
    name = "update"
    path_elem = "updates"
    _template = {'update': """function(doc, req) {

}"""}

class Validation(Generator):
    name = "validation"
    path_elem = "validate_doc_update"
    _template = {'validation': """function(newDoc, oldDoc, userCtx) {
  throw({forbidden : 'no way'});
}"""}

class GitHook(Generator):
    """
    Write a post commit git hook such that situp.py push is called after git
    commit.
    """
    name = "githook"
    path_elem = ".git/hooks"
    _template = {'githook': './situp.py push'}

    def _push_template(self, path, args, options):
        file = os.path.join(path, 'post-commit')
        self._write_file(file, self._template[self.name])
        os.chmod(file, stat.S_IXUSR | stat.S_IWUSR | stat.S_IRUSR)
        self.logger.info("Created post-commit hook in %s" % file)

class Document(Generator):
    """
    Create an empty json document (containing just an _id) in the _docs folder
    of the application root.
    """
    name = 'document'
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
    name = 'html'
    path_elem = '_attachments'
    _template = {
        'document': '<html><head><title>REPLACE</title></head><body><h1>REPLACE</h1></body></html>'
    }
    required_opts = ['name']

    def _add_options(self):
        self.parser.add_option("--name",
                    dest="name", help="Name the document")

    def _push_template(self, path, args, options):
        file_name = '%s.html' % options.name.split('.htm')[0]

        doc = self._template['document'].replace('REPLACE', options.name.split('.htm')[0].title())
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

class FetchVendors(Generator):
    """
    Vendors are generators that download external code into the right place.
    The code is held in kanso packages, and situp assumes that these have been
    correctly built.
    """

    name = "vendor"

    def __call__(self, args, options):
        """
        Override call here - need to pass in the args/options instead of get
        them from optparse.
        """
        self._configure_logger(options)

        self.logger.debug('called')
        self.logger.debug(args)
        self.logger.debug(options)

        self.run_command(args, options)

    def install_external(self, external, options, vendor_path=None):
        """ Install external """
        if not vendor_path:
            vendor_path = self._create_path(options.root, options.design)
        path = self._create_path(vendor_path, [], external)

        self.logger.debug('Installing %s into %s' % (external, path))
        # TODO: catch not founds etc
        url = "http://kan.so/repository/%s" % external
        (filename, response) = urllib.urlretrieve(url)
        package = json.load(open(filename))
        version = options.ext_version

        if version == 'latest':
            version = package['tags']['latest']
        if 'dependencies' in package['versions'][version] and\
                len(package['versions'][version]['dependencies']) > 0:
            self.logger.info('Fetching dependencies for %s' % external)
            for dep in package['versions'][version]['dependencies'].keys():
                if dep not in os.listdir(vendor_path):
                    opt = options
                    # TODO: work out the right version for a dependency
                    opt.ext_version = 'latest'
                    self.install_external(dep, options, vendor_path)
        archive = "%s-%s.tar.gz" % (external, version)
        fetch_archive(url + '/' + archive, path)
        self.logger.info("Installed %s to %s" % (external, path))


    def run_command(self, args, options):
        """
        Vendors behave differently to other generators
        """
        self.logger.warning("Fetching externals, may take a while")
        for external in args:
            self.install_external(external, options)

if __name__ == "__main__":

    cli = CommandDispatch()
    for command in [AddServer, Push, Fetch, InstallVendor, View, ListGen, Show,
            Document, Html, GitHook, Filter, Update, Validation]:
        cli.register_command(command())


    if len(sys.argv) > 1 and sys.argv[1] in cli.commands.keys():
        cli(sys.argv[1])
    else:
        cli()

