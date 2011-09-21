#!/usr/bin/env python
# encoding: utf-8

from situp import Command

class MyCommand(Command):
    command_name = 'child'
    def run_command(self, args=None, options=None):
        print 'Hello, right options:', not options.child

    def _add_options(self):
        self.parser.add_option("--me",
                    action="store_true", dest="child", default=False)
        Command._add_options(self)

class MyParentCommand(Command):
    command_name = 'parent'
    def run_command(self, args=None, options=None):
        Command.run_command(self, args, options)

    def _add_options(self):
        self.parser.add_option("--parent",
                    action="store_true", dest="parent", default=False)
        Command._add_options(self)

    def register_sub_commands(self):
        self.sub_commands['child'] = MyCommand()

class MyGrandParentCommand(Command):
    command_name = 'grandparent'
    def run_command(self, args=None, options=None):
        Command.run_command(self, args, options)

    def _add_options(self):
        self.parser.add_option("--grandparent",
                    action="store_true", dest="grandparent", default=False)
        Command._add_options(self)

    def register_sub_commands(self):
        self.sub_commands['parent'] = MyParentCommand()

if __name__ == "__main__":
    test = MyGrandParentCommand()
    test() #args=['parent', 'child'])
