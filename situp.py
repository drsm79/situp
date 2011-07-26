from optparse import OptionParser, OptionGroup
import json
import httplib
import os
import sys
import logging
import urllib
import tarfile
import zipfile
import shutil
from collections import namedtuple

class Command:
    """
    A command has a name, an option parser and a dictionary of sub commands it
    can call.
    """
    command_name = "interface"
    no_required_args = 0
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
        self._add_options()

    def __call__(self, logger=None, args=None, options=None):
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
        print args
        if len(args) and args[0] not in self.sub_commands.keys():
            self.exit_invalid("You must specify a valid command.")
        self.run_command(args, options)

    def run_command(self, args=None, options=None):
        self.sub_commands[args[0]](self.logger, args[1:], options)

    def process_args(self, args=None, options=None):
        """

        """
        if options:
            (new_options, args) = self.parser.parse_args(args=args)#, values=options)
            options._update(new_options.__dict__, 'loose')
        elif args:
            (options, args) = self.parser.parse_args(args=args)
        else:
            (options, args) = self.parser.parse_args()

        self.check_args(options, args)

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

    def check_args(self, options, args):
        """
        Check that the given arguments are right.
        """
        if not options.cmd_help:
            ok = self.no_required_args <= len(args)

            # TODO some check on required options
            if not ok:
                self.exit_invalid('')


    def exit_invalid(self, msg):
        """
        The command doesn't exist so bail
        """
        print msg
        # Described the valid commands in epilog, reuse here
        print self.parser.epilog
        sys.exit(-1)

class SitUp(Command):
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
        sub_commands = [Create(), InstallVendor(), Push(), Fetch()]
        self._register(sub_commands)

class Push(Command):
    def __call__(self, logger, args, options):
        logger.debug('pushing application')

class Fetch(Command):
    def __call__(self, logger, args, options):
        """
        Pull a design document into the application
        """
        logger.debug('fetching application')

class Create(Command):
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

    def register_sub_commands(self):
        """
        Set up the sub_commands and the OptionParser.
        """
        self._register([ View(), ListGen(), Show(), Design(), App() ])

        commands = sorted(self.sub_commands.keys())
        self.parser.epilog = "Valid entities are: %s" % ", ".join(commands)

class InstallVendor(Command):
    command_name = "vendor"
    no_required_args = 1

    def _add_options(self):
        group = OptionGroup(self.parser, "Vendor options",
                            "You can install vendors from non-standard "
                            "locations by specifying the URL on the command"
                            " line")
        for vendor in self.sub_commands.values():
            for external, url in vendor._template.items():
                group.add_option("--%s" % external, metavar="URL",
                            dest="alt_%s" % external, default=False,
                            help="Download %s from URL instead of the default [%s]"\
                                % (external, url))
        self.parser.add_option_group(group)

    def register_sub_commands(self):
        """
        Set up the sub_commands and the OptionParser.
        """
        self._register([ Backbone() ])

        commands = sorted(self.sub_commands.keys())
        self.parser.epilog = "Valid vendors are: %s" % ", ".join(commands)

class Generator(Command):
    """
    A generator knows how to create files and where to create them.
    """
    # _template is a dict of filename:it's content
    _template = {}
    # the type of thing the generator generates
    command_name = "generator_interface"
    def __init__(self):
        self.usage = "usage: %prog create " + self.command_name + " [options]"
        Command.__init__(self)

    def run_command(self, options):
        """
        Run the generator
        """
        self.process_args(args, options)
        path = self._create_path(options.root, options.design, args[0])
        self._push_template(path, args, options)

    def _create_path(self, root, design, name):
        """
        Create the path the generator needs
        """
        if os.path.exists(root):
            path_elems =[root]
            if len(design) > 1:
                path_elems.extend(design)
            path_elems.extend([self.command_name, name])
            path = os.path.join(*tuple(path_elems))
            self.logger.debug('Creating: %s' % path)
            if not os.path.exists(path):
                os.makedirs(path)
            return path
        else:
            raise OSError('Application directory (%s) does not exist' % root)

    def _write_file(self, path, content):
        f = open(path, 'w')
        f.write(content)
        f.write('\n')
        f.close()

    def _push_template(self, path, args, options):
        """
        Create files following _templates
        """
        raise NotImplementedError

class View(Generator):
    command_name = "view"
    _template = {
        'map.js': '''function(doc){
  emit(null, 1)
}''',
        'reduce.js': '''function(key, values, rereduce){

}''',
    }

    def _add_options(self):
        self.parser.add_option("--builtin-reduce",
                    dest="built_in", default=False,
                    choices=['sum', 'count', 'stats'],
                    help="Use a built in reduce (one of sum, count, stats)")

    def _push_template(self, path, args, options):
        """
        Create files following _templates, built_in should be either unset
        (False) or be the name of a built in reduce function.
        """

        reduce_file = os.path.join(path, 'reduce.js')
        map_file = os.path.join(path, 'map.js')

        self._write_file(map_file, self._template['map.js'])
        if options.built_in:
            # Not sure I like this...
            built_in = options.built_in.strip('_')
            # Generate a reduce function which uses a built in
            if built_in in built_in_reduces:
                self._write_file(reduce_file, '_%s' % built_in)
            else:
                raise KeyError('%s is not a built in reduce' % built_in)
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

def fetch_archive(url, path, filter_list=[]):
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
    command_name = 'backbone'
    _template = {
        'backbone' : Package('https://github.com/documentcloud/backbone/zipball/master', ['backbone.js']),
        'backbone.couch' : Package('https://github.com/mikewallace1979/backbone-couch/tarball/master', ['backbone.couch.js']),
        'underscore' : Package('https://github.com/documentcloud/underscore/tarball/master', ['underscore-min.js'])
    }

class YUI(Vendor):
    command_name = 'yui'
    _template = {}

class Evently(Vendor):
    command_name = 'evently'
    _template = {}



if __name__ == "__main__":
    situp = SitUp()
    situp()
