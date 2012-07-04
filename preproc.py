"""
Preprocessors are run before the Push command. They are called with the same
args and options as Push and the command's logger, so should be able to
determine context and log appropriately.

Preprocessors should be used for 'compile' like tasks and status checks.
"""
from subprocess import Popen as _call
from subprocess import PIPE as _STDOUT
import os as _os
import json as _json

def _external(cmd, logger, msg):
  """
  Run an external command with appropriate logging (e.g. if command isn't
  installed)
  """
  logger.debug('%s: %s' % (msg, cmd))
  p = _call(cmd, stdout=_STDOUT)
  return p.communicate()

def example(args, options, logger):
  """
  A trivial example preprocessor
  """
  logger.info('[EXAMPLE] %s' % args)
  logger.info('[EXAMPLE] %s' % options)
