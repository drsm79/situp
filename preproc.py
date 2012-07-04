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


def _compile_md(markdown, path, logger, fn):
  """
  Call the markdown compiler, then run a callback with the result.
  """

  all_docs = _os.listdir(path)
  for md in filter(lambda x: x.endswith('.md'), all_docs):
    md_name = md.split('.')[0]
    cmd  = []
    cmd.extend(markdown)
    cmd.append(_os.path.join(path, md))
    result = _external(cmd, logger, "[MARKDOWN] compiling")
    fn(path, md_name, result)


def markdown(args, options, logger):
  """
  Run the markdown 'compiler' for all .md files in _docs and _attachments. Call
  the preprocessor with the markdown command you want to run, for example:

    situp.py push -e foo -s https://localhost:5984 --pre=markdown "perl /path/to/Markdown.pl --html4tags"

  Markdown in _docs is turned into json with _id matching the filename and
  a single key called content, containing the compiled markdown.

  Markdown in a design's _attachments directory is rendered into html files
  named after the .md file. If there is a header.html or footer.html these are
  concatenated onto the generated html markup.

  The generated html/json is not cleaned up after running, but will be
  overwritten on a subsequent invocation.
  """

  markdown = args[0].split(' ')

  logger.debug('[MARKDOWN] using %s as compile command' % markdown)
  docs = _os.path.join(options.root, '_docs')
  designs = _os.path.join(options.root, '_design')

  if _os.path.exists(docs):
    def _md_to_json(path, filename, result):
      j = {'_id': filename, 'content': result[0]}
      _json.dump(j, open(_os.path.join(path, '%s.json' % filename), 'w'))

    _compile_md(markdown, docs, logger, _md_to_json)

  if _os.path.exists(designs):
    def _md_to_html(path, filename, result):
      f = open(_os.path.join(path, '%s.html' % filename), 'w')
      f.write(header)
      f.write(result[0])
      f.write(footer)
      f.close()

    for design in _os.listdir(designs):
      designpath = _os.path.join(designs, design, '_attachments')
      logger.debug('[MARKDOWN] %s' % designpath)
      header = '<html><head></head><body>'
      footer = '</body></html>'
      header_f = _os.path.join(designpath, 'header.html')
      if _os.path.exists(header_f):
        logger.debug('Ladies and gentlemen we have a header')
        header = open(header_f).read()

      footer_f = _os.path.join(designpath, 'footer.html')
      if _os.path.exists(footer_f):
        logger.debug('Ladies and gentlemen we have a footer')
        footer = open(footer_f).read()

      _compile_md(markdown, designpath, logger, _md_to_html)

