# -*- coding: utf-8 -*-

# Public Domain (-) 2010-2016 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

"""GitFund Python Services."""

import logging
import os
import sys

from json import loads as decode_json, dumps as encode_json
from os.path import dirname
from traceback import format_exception
from urllib import unquote as urlunquote

# Extend the sys.path to include the parent directory and ``lib``.
sys.path.insert(0, dirname(__file__))
sys.path.insert(0, 'lib')

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer

from config import SECRET_KEY

# ------------------------------------------------------------------------------
# HTTP Constants
# ------------------------------------------------------------------------------

HTML_RESPONSE = """<!DOCTYPE html>
<meta charset=utf-8>
<title>%(msg)s</title>
<link href='//fonts.googleapis.com/css?family=Droid+Sans' rel=stylesheet>
<style>
body {
  font-family: 'Droid Sans', Verdana, sans-serif;
  font-size: 40px;
  padding: 10px 7px;
}
</style>
<body>
%(msg)s
"""

ERROR_400 = HTML_RESPONSE % dict(msg="400 Bad Request")
ERROR_401 = HTML_RESPONSE % dict(msg="401 Not Authorized")
ERROR_404 = HTML_RESPONSE % dict(msg="404 Not Found")
ROOT_HTML = HTML_RESPONSE % dict(msg="Python API Endpoint")

RESPONSE_HEADERS_HTML = [("Content-Type", "text/html; charset=utf-8")]
RESPONSE_OPT = ("200 OK", [("Allow:", "OPTIONS, GET, HEAD, POST")])
RESPONSE_200 = ("200 OK", RESPONSE_HEADERS_HTML)
RESPONSE_400 = ("400 Bad Request", RESPONSE_HEADERS_HTML)
RESPONSE_401 = ("401 Unauthorized", RESPONSE_HEADERS_HTML +
                [("WWW-Authenticate", "Token realm='Service', error='invalid_auth'")])
RESPONSE_404 = ("404 Not Found", RESPONSE_HEADERS_HTML)
RESPONSE_501 = ("501 Not Implemented", [])

SUPPORTED_HTTP_METHODS = frozenset(['GET', 'HEAD', 'POST'])

# ------------------------------------------------------------------------------
# Service Utilities
# ------------------------------------------------------------------------------

SERVICE_REGISTRY = {}

# The ``service`` decorator is used to turn a handler function into a service.
def service(handler):
    SERVICE_REGISTRY[handler.__name__] = handler
    return handler

# ------------------------------------------------------------------------------
# App Runner
# ------------------------------------------------------------------------------

def app(
    env, start_response, dict=dict, isinstance=isinstance, ord=ord,
    in_production=os.environ.get('SERVER_SOFTWARE', '').startswith('Google'),
    secret_len=len(SECRET_KEY), unicode=unicode, urlunquote=urlunquote
    ):

    http_method = env['REQUEST_METHOD']
    def respond(prelude, content=None):
        if http_method == 'HEAD':
            if content:
                headers = prelude[1] + [("Content-Length", str(len(content)))]
                start_response(prelude[0], headers)
            else:
                start_response(*prelude)
            return []
        start_response(*prelude)
        return [content]

    if http_method == 'OPTIONS':
        return respond(RESPONSE_OPT)

    if http_method not in SUPPORTED_HTTP_METHODS:
        return respond(RESPONSE_501)

    if in_production and env['wsgi.url_scheme'] != 'https':
        return respond(RESPONSE_401, ERROR_401)

    args = filter(None, env['PATH_INFO'].split('/'))
    if not args:
        return respond(RESPONSE_200, ROOT_HTML)

    if (len(args) != 2) or args[0] != '.python':
        return respond(RESPONSE_404, ERROR_404)

    service = args[1]
    if service not in SERVICE_REGISTRY:
        return respond(RESPONSE_404, ERROR_404)

    if http_method != 'POST':
        return respond(RESPONSE_400, ERROR_400)

    handler = SERVICE_REGISTRY[service]
    kwargs = {}

    body = env['wsgi.input'].read()
    if len(body) < secret_len:
        return respond(RESPONSE_401, ERROR_401)

    auth = body[:secret_len]
    total = 0
    for x, y in zip(auth, SECRET_KEY):
        total |= ord(x) ^ ord(y)
    if total != 0:
        return respond(RESPONSE_401, ERROR_401)

    body = body[secret_len:]
    if body:
        try:
            kwargs = decode_json(body)
        except:
            logging.error(u''.join(format_exception(*sys.exc_info())))
            return respond(RESPONSE_400, ERROR_400)

    try:
        content = dict(result=handler(**kwargs))
    except Exception, error:
        logging.error(u''.join(format_exception(*sys.exc_info())))
        content = dict(
            error=(u"%s: %s" % (error.__class__.__name__, error))
            )

    content = encode_json(content)
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(content)))
    ]

    start_response("200 OK", headers)
    return [content]

# -----------------------------------------------------------------------------
# Services
# -----------------------------------------------------------------------------

@service
def hilite(code, lang=None):
    if lang:
        try:
            lexer = get_lexer_by_name(lang)
        except ValueError:
            lang = 'txt'
            lexer = TextLexer()
    else:
        lang = 'txt'
        lexer = TextLexer()
    formatter = HtmlFormatter(
        cssclass='syntax %s' % lang, lineseparator='<br/>'
        )
    return highlight(code, lexer, formatter)
