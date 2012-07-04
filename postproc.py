"""
Postprocessors are run after the Push command. They are called with the same
args and options as Push and the command's logger, so should be able to
determine context and log appropriately.

Postprocessors should be used for 'clean' like tasks and deployment validation.
"""
from preproc import _external
import os as _os

def example(args, options, logger):
  """
  A trivial example preprocessor
  """
  logger.info('[EXAMPLE] %s' % args)
  logger.info('[EXAMPLE] %s' % options)