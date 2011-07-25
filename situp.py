from optparse import OptionParser
import json
import httplib
import os
import sys
import logging


class Command:
    """
    A command has a name, an option parser and a dictionary of sub commands it
    can call.
    """
    command_name = "interface"
    no_required_args = 0
    dependencies = []
    def __init__(self, parser=None, sub_command=False):
        """
        Initialise the OptionParser for the Command.
        """
        self.sub_commands = {}
        # Need to deal with competing OptionParsers...
        if parser:
            self.parser = parser
        elif sub_command:
            self.parser = OptionParser(add_help_option=False)
        else:
            self.parser = OptionParser()
        self.register_sub_commands()

    def __call__(self, logger=None, args=None, options=None):
        """
        call the command
        """
        if args or options:
            self.parser.parse_args(args=args, values=options)
        (options, args) = self.parser.parse_args()
        if logger:
            self.logger = logger
        else:
            logging.basicConfig()
            options.logger = logging.getLogger('situp')
        if options.quiet:
            options.logger.setLevel(logging.CRITICAL)
        elif options.debug:
            options.logger.setLevel(logging.DEBUG)
        #Should set up a logger and write these to it's debug stream
        if not self.check_args(args) or args[0] not in self.sub_commands.keys():
            print "You must specify a valid command."
            # Described the valid commands in epilog, reuse here
            print self.parser.epilog
            sys.exit(-1)
        if options.cmd_help:
            # call the print_help function for the command
            self.sub_commands[args[0]].print_help()
        else:
            # run the command
            self.sub_commands[args[0]](options.logger, args[1:], options)

    def _add_options(self):
        """
        Add options to the command's option parser
        """
        pass

    def register_sub_commands(self):
        """
        Initialise generator classes for the command and update the optparser
        """
        usage = "usage: %prog " + self.command_name
        usage += " [%s]" %  '|'.join(self.sub_commands.keys())
        usage += " [options] [args]"
        self.parser.set_usage(usage)

    def print_help(self):
        """
        Encapsulate the Generator's option parser's print_help() method here in
        case there's some reason to override it.

        parser.print_help() actually prints to the screen, so just run that.
        """
        self.parser.print_help()

    def check_args(self, args):
        """
        Check that the given arguments are right.
        """
        return self.no_required_args <= len(args)


class SitUp(Command):
    def _add_options(self):
        usage = "usage: %prog [options] COMMAND [options] [args]"
        commands = sorted(self.sub_commands.keys())
        epilog = "Valid commands are: %s" % ", ".join(commands)
        self.parser.set_usage(usage)
        self.parser.epilog = epilog

        # This is the important bit
        self.parser.disable_interspersed_args()

        self.parser.add_option("-q", "--quiet",
                    action="store_true", dest="quiet", default=False,
                    help="don't print any messages to stdout")

        self.parser.add_option("--debug",
                    action="store_true", dest="debug", default=False,
                    help="print extra messages to stdout")

        self.parser.add_option("--cmd-help",
                    metavar="COMMAND",
                    dest="cmd_help",
                    action="store_true", default=False,
                    help="print help for COMMAND")

        self.parser.add_option("-d", "--design",
                    metavar="DESIGN",
                    dest="design",
                    help="modify the design document DESIGN")

        pwd = os.getcwd()
        self.parser.add_option("-r", "--root",
                    dest="root", default=pwd,
                    help="Application root directory, default is %s" % pwd)

    def register_sub_commands(self):
        create = Create(self.parser)
        self.sub_commands[create.command_name] = create

    def __call__(self):
        (options, args) = self.parser.parse_args()
        logging.basicConfig()
        options.logger = logging.getLogger('situp')
        if options.quiet:
            options.logger.setLevel(logging.CRITICAL)
        elif options.debug:
            options.logger.setLevel(logging.DEBUG)
        #Should set up a logger and write these to it's debug stream
        if len(args) == 0 or args[0] not in self.sub_commands.keys():
            print "You must specify a valid command."
            # Described the valid commands in epilog, reuse here
            print self.parser.epilog
            sys.exit(-1)
        if options.cmd_help:
            # call the print_help function for the command
            self.sub_commands[args[0]].print_help()
        else:
            # run the command
            self.sub_commands[args[0]](options.logger, args[1:], options)

class Create(Command):
    command_name = "create"
    no_required_args = 2

    def _add_options(self):
        """
        Create commands can add the created documents to an index
        """
        self.parser.add_option("--index",
                dest="index",
                action="store_true", default=False,
                help="modify the design document DESIGN")

    def register_generators(self):
        """
        Set up the OptionParser.
        """
        self.usage = "usage: %prog " + self.command_name
        self.usage += " [%s]" %  '|'.join(self.generators.keys())
        self.usage += " design name [options]"

        self.sub_commands['view'] = View(self.parser)
        self.sub_commands['list'] = ListGen(self.parser)
        self.sub_commands['show'] = Show(self.parser)

class Generator:
    """
    A generator knows how to create files and where to create them.
    """
    # _template is a dict of filename:it's content
    _template = {}
    # the type of thing the generator generates
    _gen_type = "interface"

    def __init__(self, opt_parser):
        """
        Generators can add options to the calling commands option parser
        """
        self.opt_parser = opt_parser
        self._add_options()

    def _add_options(self):
        """
        Add options to the option parser passed in to the Generators constructor
        """
        pass

    def __call__(self, logger, args, options):
        """
        Run the generator
        """
        self.logger = logger
        path = self._create_path(options.root, args[0], args[1])
        self._push_template(path, args, options)

    def _create_path(self, root, design, name):
        """
        Create the path the generator needs
        """
        if os.path.exists(root):
            path = os.path.join(root, design, self._gen_type, name)
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
    _gen_type = "view"

    _template = {
        'map.js': '''function(doc){
  emit(null, 1)
}''',
        'reduce.js': '''function(key, values, rereduce){

}''',
    }

    def _add_options(self):
        self.opt_parser.add_option("--builtin-reduce",
                    dest="built_in", default=False,
                    help="Use a built in reduce (one of sum, count, stats)")

    def _push_template(self, path, args, options):
        """
        Create files following _templates, built_in should be either unset
        (False) or be the name of a built in reduce function.
        """
        built_in_reduces = ['sum', 'count', 'stats']

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
    _gen_type = "list"

class Show(Generator):
    _gen_type = "show"

class Filter(Generator):
    _gen_type = "filter"

if __name__ == "__main__":
    situp = SitUp()
    situp()
