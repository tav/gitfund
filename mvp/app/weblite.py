# Public Domain (-) 2008-2016 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

"""A sexy micro-framework for use with Google App Engine."""

import logging
import os
import sys

from BaseHTTPServer import BaseHTTPRequestHandler
from binascii import hexlify
from cgi import FieldStorage
from Cookie import SimpleCookie
from cStringIO import StringIO
from datetime import datetime
from hashlib import md5
from json import loads as json_decode
from os import urandom
from os.path import dirname, exists, join, getmtime, realpath
from threading import local
from traceback import format_exception
from urllib import quote as urlquote, urlencode, unquote as urlunquote
from urlparse import urljoin
from wsgiref.headers import Headers

from google.appengine.ext.blobstore import parse_file_info
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

APP_ROOT = realpath(dirname(__file__))

# Extend the sys.path to include the parent and ``lib`` sibling directories.
sys.path.insert(0, APP_ROOT)
sys.path.insert(0, 'lib')

from mako.exceptions import RichTraceback
from mako.template import Template as MakoTemplate

from tavutil.exception import html_format_exception
from tavutil.crypto import (
    create_tamper_proof_string, secure_string_comparison,
    validate_tamper_proof_string
    )

from webob import Request as WebObRequest # this import patches cgi.FieldStorage
                                          # to behave better for us too!

from config import (
    ALTERNATIVE_HOSTS, CANONICAL_HOST, DEBUG, SECURE_COOKIE_DURATION,
    SECURE_COOKIE_KEY, STATIC_HANDLER, TASK_AUTH
    )

# ------------------------------------------------------------------------------
# Utility File Reader
# ------------------------------------------------------------------------------

def read(file):
    f = open(file, 'rb')
    data = f.read()
    f.close()
    return data

# ------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------

COOKIE_KEY_NAMES = frozenset([
    'domain', 'expires', 'httponly', 'max-age', 'path', 'secure', 'version'
    ])

HTTP_STATUS_MESSAGES = BaseHTTPRequestHandler.responses

RESPONSE_NOT_IMPLEMENTED = ("501 Not Implemented", [])
RESPONSE_OPTIONS = (
    "200 OK",
    [("Allow:", "OPTIONS, GET, HEAD, POST")]
    )

RESPONSE_HEADERS_HTML = [
    ("Content-Type", "text/html; charset=utf-8")
]

STATUS_301 = "301 Moved Permanently"
STATUS_302 = "302 Found"

RESPONSE_401 = ("401 Unauthorized", RESPONSE_HEADERS_HTML +
                [("WWW-Authenticate", "Token realm='Service', error='token_expired'")])
RESPONSE_403 = ("403 Forbidden", RESPONSE_HEADERS_HTML)
RESPONSE_404 = ("404 Not Found", RESPONSE_HEADERS_HTML)
RESPONSE_500 = ("500 Server Error", RESPONSE_HEADERS_HTML)
RESPONSE_503 = ("503 Service Unavailable", RESPONSE_HEADERS_HTML)

if os.environ.get('SERVER_SOFTWARE', '').startswith('Google'):
    RUNNING_ON_GOOGLE_SERVERS = True
else:
    RUNNING_ON_GOOGLE_SERVERS = False

HANDLERS = {}
SUPPORTED_HTTP_METHODS = frozenset(['GET', 'HEAD', 'POST'])

VALID_REQUEST_CONTENT_TYPES = frozenset([
    '', 'application/x-www-form-urlencoded', 'multipart/form-data'
    ])

# ------------------------------------------------------------------------------
# Default Error Templates
# ------------------------------------------------------------------------------

try:

    from config import (
        ERROR_401, ERROR_403, ERROR_404, ERROR_500, ERROR_500_TRACEBACK,
        ERROR_503
        )

except ImportError:

    ERROR_WRAPPER = """<!DOCTYPE html>
<meta charset=utf-8>
<title>Error!</title>
<link rel=stylesheet href=/%s/site.css>
<body>
%%s
""" % STATIC_HANDLER

    ERROR_401 = ERROR_WRAPPER % """
  <div class="site-error">
    <h1>Not Authorized</h1>
    Your session may have expired or you may not have access.
    <ul>
      <li><a href="/">Return home</a></li>
      <li><a href="/login">Login</a></li>
    </ul>
  </div>
  """ # emacs"

    ERROR_403 = ERROR_WRAPPER % """
  <div class="site-error">
    <h1>Forbidden</h1>
    <ul>
      <li><a href="/">Return home</a></li>
      <li><a href="/login">Login</a></li>
    </ul>
  </div>
  """ # emacs"

    ERROR_404 = ERROR_WRAPPER % """
  <div class="site-error">
    <h1>The item you requested was not found</h1>
    You may have clicked a dead link or mistyped the address. Some web addresses
    are case sensitive.
    <ul>
      <li><a href="/">Return home</a></li>
    </ul>
  </div>
  """ # emacs"

    ERROR_500_BASE = ERROR_WRAPPER % """
  <div class="site-error">
    <h1>Sorry, something went wrong!</h1>
    There was an application error. This has been logged and will be resolved as
    soon as possible.
    <ul>
      <li><a href="/">Return home</a></li>
    </ul>
    %s
  </div>
  """ # emacs"

    ERROR_500 = ERROR_500_BASE % ""

    ERROR_500_TRACEBACK = ERROR_500_BASE % """
    <div class="traceback">%s</div>
  """ # emacs"

    ERROR_503 = ERROR_WRAPPER % """
  <div class="site-error">
    <h1>Service Unavailable</h1>
    Google App Engine is currently down for a scheduled maintenance.
    Please try again later.
    <ul>
      <li><a href="/">Return home</a></li>
    </ul>
  </div>
  """ # emacs"

# ------------------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------------------

# Handlers can throw exceptions to return specifc HTTP response codes.
#
# All the errors subclass the ``BaseHTTPError``.
class BaseHTTPError(Exception):
    pass

# The ``Redirect`` exception is used to handle HTTP 301/302 redirects.
class Redirect(BaseHTTPError):
    def __init__(self, uri, permanent=False):
        self.uri = urljoin('', str(uri))
        self.permanent = permanent

# The ``HTTPContent`` is used to return the associated content.
class HTTPContent(BaseHTTPError):
    def __init__(self, content):
        self.content = content

# The ``AuthError`` is used to represent the 401 Not Authorized error.
class AuthError(BaseHTTPError):
    pass

# The ``NotFound`` is used to represent the classic 404 error.
class NotFound(BaseHTTPError):
    pass

# The ``HTTPError`` is used to represent all other response codes.
class HTTPError(BaseHTTPError):
    def __init__(self, code=500):
        self.code = code

# ------------------------------------------------------------------------------
# Static
# ------------------------------------------------------------------------------

def STATIC(path, cache={}, assets=json_decode(read('assets.json'))):
    if path in cache:
        return cache[path]
    return cache.setdefault(path, "/%s/%s" % (STATIC_HANDLER, assets[path]))

# ------------------------------------------------------------------------------
# Handler Utilities
# ------------------------------------------------------------------------------

try:
    from config import SSL_ONLY
except ImportError:
    SSL_ONLY = True

HANDLER_DEFAULT_CONFIG = {
    'admin': False,
    'anon': True,
    'blob': False,
    'cache': None,
    'cron': None,
    'post_encoding': False,
    'ssl': SSL_ONLY,
    'task': None,
    'xsrf': False
    }

# The ``handle`` decorator is used to turn a function into a handler.
def handle(name=None, renderers=[], **config):
    if isinstance(name, (list, tuple)) and renderers == []:
        renderers = name
        name = None
    def __register_handler(function):
        parse_cache_config(config)
        __config = HANDLER_DEFAULT_CONFIG.copy()
        __config.update(config)
        if not name:
            _name = '.'.join(function.__name__.split('_'))
            if _name.startswith('cron.'):
                __config['cron'] = True
            elif _name.startswith('task.'):
                __config['task'] = True
            HANDLERS[_name] = (function, renderers, __config)
        else:
            for _name in name.split():
                if _name.startswith('cron.'):
                    __config['cron'] = True
                elif _name.startswith('task.'):
                    __config['task'] = True
                HANDLERS[_name] = (function, renderers, __config)
        return function
    if hasattr(name, '__call__'):
        function = name
        name = None
        return __register_handler(function)
    return __register_handler

def parse_cache_config(cfg, valid_values=set(['public', 'private', 'no-cache'])):
    if 'cache' not in cfg:
        return
    cache = cfg.pop('cache')
    if not cache:
        return
    if isinstance(cache, tuple):
        cache, duration = cache
    else:
        duration = 864000
    if cache not in valid_values:
        raise ValueError("invalid cache configuration: %s" % cache)
    cfg['cache'] = (cache, duration)

# ------------------------------------------------------------------------------
# HTTP Utilities
# ------------------------------------------------------------------------------

# Return an HTTP header date/time string.
def get_http_datetime(timestamp=None):
    if timestamp:
        if not isinstance(timestamp, datetime):
            timestamp = datetime.fromtimestamp(timestamp)
    else:
        timestamp = datetime.utcnow()
    return timestamp.strftime('%a, %d %B %Y %H:%M:%S GMT') # %m

# ------------------------------------------------------------------------------
# Context
# ------------------------------------------------------------------------------

# The ``Context`` class encompasses the HTTP request/response. An instance,
# specific to the current request, is passed in as the first parameter to all
# handlers.
class Context(object):

    DEBUG = DEBUG
    STATIC = staticmethod(STATIC)

    urlencode = staticmethod(urlencode)
    urlquote = staticmethod(urlquote)
    urlunquote = staticmethod(urlunquote)

    end_pipeline = None
    site_host = None

    _cookies_parsed = None
    _xsrf_token = None

    after_runners = []

    def __init__(self, name, environ, ssl_mode):
        self.name = name
        self.environ = environ
        self.host = environ['HTTP_HOST']
        self._status = (200, 'OK')
        self._raw_headers = []
        self._response_cookies = {}
        self.response_headers = Headers(self._raw_headers)
        self.ssl_mode = ssl_mode
        if ssl_mode:
            self.scheme = 'https'
        else:
            self.scheme = 'http'

    def set_response_status(self, code, message=None):
        if not message:
            message = HTTP_STATUS_MESSAGES.get(code, ["Server Error"])[0]
        self._status = (code, message)

    def _parse_cookies(self):
        cookies = {}
        cookie_data = self.environ.get('HTTP_COOKIE', '')
        if cookie_data:
            _parsed = SimpleCookie()
            _parsed.load(cookie_data)
            for name in _parsed:
                cookies[name] = _parsed[name].value
        self._request_cookies = cookies
        self._cookies_parsed = 1

    def get_cookie(self, name, default=''):
        if not self._cookies_parsed:
            self._parse_cookies()
        return self._request_cookies.get(name, default)

    def get_secure_cookie(self, name, key=SECURE_COOKIE_KEY, timestamped=True):
        if not self._cookies_parsed:
            self._parse_cookies()
        if name not in self._request_cookies:
            return
        return validate_tamper_proof_string(
            name, self._request_cookies[name], key, timestamped
            )

    def set_cookie(self, name, value, **kwargs):
        cookie = self._response_cookies.setdefault(name, {})
        cookie['value'] = value
        kwargs.setdefault('path', '/')
        if self.ssl_mode:
            kwargs.setdefault('secure', 1)
        for name, value in kwargs.iteritems():
            if value:
                cookie[name.lower()] = value

    def set_secure_cookie(
        self, name, value, key=SECURE_COOKIE_KEY,
        duration=SECURE_COOKIE_DURATION, **kwargs
        ):
        value = create_tamper_proof_string(name, value, key, duration)
        self.set_cookie(name, value, **kwargs)

    def append_to_cookie(self, name, value):
        cookie = self._response_cookies.setdefault(name, {})
        if 'value' in cookie:
            cookie['value'] = '%s:%s' % (cookie['value'], value)
        else:
            cookie['value'] = value

    def expire_cookie(self, name, **kwargs):
        if name in self._response_cookies:
            del self._response_cookies[name]
        kwargs.setdefault('path', '/')
        kwargs.update({'max_age': 0, 'expires': "Fri, 31-Dec-99 23:59:59 GMT"})
        self.set_cookie(name, '', **kwargs)

    def cache_private_response(self, etag, duration=864000):
        if self.environ['REQUEST_METHOD'] == 'POST':
            return
        etag = '"%s"' % etag
        resp = self.response_headers
        resp['Etag'] = etag
        resp['Cache-Control'] = "private, max-age=%d;" % duration
        if self.environ.get('HTTP_IF_NONE_MATCH') == etag:
            self.set_response_status(304)
            raise HTTPContent("")

    def cache_response(self, etag, duration=864000):
        if self.environ['REQUEST_METHOD'] == 'POST':
            return
        etag = '"%s"' % etag
        resp = self.response_headers
        resp['Etag'] = etag
        resp['Pragma'] = "Public"
        resp['Cache-Control'] = "public, max-age=%d;" % duration
        if self.environ.get('HTTP_IF_NONE_MATCH') == etag:
            self.set_response_status(304)
            raise HTTPContent("")

    def do_not_cache_response(self):
        headers = self.response_headers
        headers['Expires'] = "Fri, 31 December 1999 23:59:59 GMT"
        headers['Cache-Control'] = "no-store, must-revalidate" # HTTP/1.1
        headers['Pragma'] = "no-cache"                         # HTTP/1.0

    def check_task_auth(self, kwargs):
        if not self.is_admin:
            raise NotFound
        if '__auth__' not in kwargs:
            raise NotFound
        auth = kwargs.pop('__auth__')
        if not secure_string_comparison(auth, TASK_AUTH):
            raise NotFound

    def compute_url(self, *args, **kwargs):
        return self.compute_url_for_host(self.site_host or self.host, *args, **kwargs)

    def compute_url_for_host(self, host, *args, **kwargs):
        out = self.scheme + '://' + host + '/' + '/'.join(
            arg.encode('utf-8') for arg in args
            )
        if kwargs:
            out += '?'
            _set = 0
            _l = ''
            for key, value in kwargs.items():
                key = urlquote(key).replace(' ', '+')
                if value is None:
                    value = ''
                if isinstance(value, list):
                    for val in value:
                        if _set: _l = '&'
                        out += '%s%s=%s' % (
                            _l, key,
                            urlquote(val.encode('utf-8')).replace(' ', '+')
                            )
                        _set = 1
                else:
                    if _set: _l = '&'
                    out += '%s%s=%s' % (
                        _l, key, urlquote(value.encode('utf-8')).replace(' ', '+')
                        )
                    _set = 1
        return out

    def sign_value(self, type, value, key=SECURE_COOKIE_KEY):
        return create_tamper_proof_string(type, value, key)

    def validate_value(self, type, value, key=SECURE_COOKIE_KEY):
        return validate_tamper_proof_string(type, value, key)

    @property
    def is_admin(self):
        if not hasattr(self, '_is_admin'):
            self._is_admin = self.get_admin_status()
        return self._is_admin

    @property
    def site_url(self):
        if not hasattr(self, '_site_url'):
            if self.site_host:
                self._site_url = self.scheme + '://' + self.site_host
            else:
                self._site_url = self.scheme + '://' + self.host
        return self._site_url

    @property
    def url(self):
        if not hasattr(self, '_url'):
            self._url = self.site_url + self.environ['PATH_INFO']
        return self._url

    @property
    def url_with_qs(self):
        if not hasattr(self, '_url_with_qs'):
            env = self.environ
            query = env['QUERY_STRING']
            self._url_with_qs = (
                self.site_url + env['PATH_INFO'] + (
                    query and '?' or '') + query
                )
        return self._url_with_qs

    @property
    def user(self):
        if not hasattr(self, '_user'):
            self._user = self.get_user()
        return self._user

    @property
    def user_id(self):
        if not hasattr(self, '_user_id'):
            self._user_id = self.get_user_id()
        return self._user_id

    def validate_xsrf(self, token):
        if not secure_string_comparison(token, self.xsrf_token):
            raise AuthError("XSRF token does not match.")

    @property
    def xsrf_token(self):
        if not self._xsrf_token:
            xsrf_token = self.get_secure_cookie('xsrf')
            if not xsrf_token:
                xsrf_token = hexlify(urandom(18))
                self.set_secure_cookie('xsrf', xsrf_token)
            self._xsrf_token = xsrf_token
        return self._xsrf_token

    from user import get_admin_status, get_user, get_user_id

    try:
        from user import get_login_url
    except ImportError:
        def get_login_url(self):
            return self.compute_url('login', return_to=self.url_with_qs)

    @classmethod
    def register_after_runner(klass, func):
        klass.after_runners.append(func)

# ------------------------------------------------------------------------------
# App Runner
# ------------------------------------------------------------------------------

reqlocal = local()

def handle_http_request(
    env, start_response, dict=dict, isinstance=isinstance, urlunquote=urlunquote,
    unicode=unicode, get_response_headers=lambda: None
    ):

    reqlocal.template_error_traceback = None

    try:

        http_method = env['REQUEST_METHOD']
        ssl_mode = env['wsgi.url_scheme'] == 'https'

        if RUNNING_ON_GOOGLE_SERVERS and env['HTTP_HOST'] in ALTERNATIVE_HOSTS:
            if SSL_ONLY or ssl_mode:
                dest = 'https://' + CANONICAL_HOST
            else:
                dest = 'http://' + CANONICAL_HOST
            if http_method == 'GET':
                dest += env['PATH_INFO']
                query_string = env['QUERY_STRING']
                if query_string:
                    dest += '?' + query_string
            else:
                dest += '/'
            start_response(STATUS_301, [('Location', dest)])
            return []

        if http_method == 'OPTIONS':
            start_response(*RESPONSE_OPTIONS)
            return []

        if http_method not in SUPPORTED_HTTP_METHODS:
            start_response(*RESPONSE_NOT_IMPLEMENTED)
            return []

        _path_info = env['PATH_INFO']
        if isinstance(_path_info, unicode):
            _args = [arg for arg in _path_info.split(u'/') if arg]
        else:
            _args = [
                unicode(arg, 'utf-8', 'strict')
                for arg in _path_info.split('/') if arg
                ]

        if _args:
            name = _args[0]
            args = _args[1:]
        else:
            name = '/'
            args = ()

        routed = 0
        if name not in HANDLERS:
            router = handle_http_request.router
            if router:
                _info = router(env, _args)
                if not _info:
                    logging.error("No handler found for: %s" % _path_info)
                    raise NotFound
                name, args = _info
                routed = 1
            else:
                logging.error("Handler not found: %s" % name)
                raise NotFound

        handler, renderers, config = HANDLERS[name]
        kwargs = {}

        ctx = Context(name, env, ssl_mode)
        ctx.was_routed = routed

        for part in [
            sub_part
            for part in env['QUERY_STRING'].lstrip('?').split('&')
            for sub_part in part.split(';')
            ]:
            if not part:
                continue
            part = part.split('=', 1)
            if len(part) == 1:
                value = None
            else:
                value = part[1]
            key = urlunquote(part[0].replace('+', ' '))
            if value:
                value = unicode(
                    urlunquote(value.replace('+', ' ')), 'utf-8', 'strict'
                    )
            else:
                value = None
            kwargs[key] = value

        # Parse the POST body if it exists and is of a known content type.
        if http_method == 'POST':

            content_type = env.get('CONTENT-TYPE', '')
            if not content_type:
                content_type = env.get('CONTENT_TYPE', '')

            if ';' in content_type:
                content_type = content_type.split(';', 1)[0]

            if content_type in VALID_REQUEST_CONTENT_TYPES:

                post_environ = env.copy()
                post_environ['QUERY_STRING'] = ''

                if config['post_encoding']:
                    ctx.request_body = env['wsgi.input'].read()
                    env['wsgi.input'] = StringIO(ctx.request_body)
                    post_encoding = config['post_encoding']
                else:
                    post_encoding = 'utf-8'

                post_data = FieldStorage(
                    environ=post_environ, fp=env['wsgi.input'],
                    keep_blank_values=True
                    ).list or []

                for field in post_data:
                    key = field.name
                    if field.filename:
                        if config['blob']:
                            value = parse_file_info(field)
                        else:
                            value = field
                    else:
                        value = unicode(field.value, post_encoding, 'strict')
                    kwargs[key] = value

            elif content_type == 'application/json':
                kwargs.update(json_decode(env['wsgi.input'].read()))

        def get_response_headers():
            # Figure out the HTTP headers for the response ``cookies``.
            cookie_output = SimpleCookie()
            for name, values in ctx._response_cookies.iteritems():
                name = str(name)
                cookie_output[name] = values.pop('value')
                cur = cookie_output[name]
                for key, value in values.items():
                    if key == 'max_age':
                        key = 'max-age'
                    if key not in COOKIE_KEY_NAMES:
                        continue
                    cur[key] = value
            if cookie_output:
                raw_headers = ctx._raw_headers + [
                    ('Set-Cookie', ck.split(' ', 1)[-1])
                    for ck in str(cookie_output).split('\r\n')
                    ]
            else:
                raw_headers = ctx._raw_headers
            str_headers = []; new_header = str_headers.append
            for k, v in raw_headers:
                if isinstance(k, unicode):
                    k = k.encode('utf-8')
                if isinstance(v, unicode):
                    v = v.encode('utf-8')
                new_header((k, v))
            return str_headers

        if 'submit' in kwargs:
            del kwargs['submit']

        if RUNNING_ON_GOOGLE_SERVERS:
            if config['cron']:
                if not env.get('HTTP_X_APPENGINE_CRON'):
                    ctx.check_task_auth(kwargs)
            elif config['task']:
                if not env.get('HTTP_X_APPENGINE_TASKNAME'):
                    ctx.check_task_auth(kwargs)
            elif config['ssl'] and not ssl_mode:
                raise NotFound

        if config['xsrf']:
            if 'xsrf' not in kwargs:
                raise AuthError("XSRF token not present.")
            provided_xsrf = kwargs.pop('xsrf')
            if not secure_string_comparison(provided_xsrf, ctx.xsrf_token):
                raise AuthError("XSRF token does not match.")

        if config['admin'] and not ctx.is_admin:
            if ctx.user_id:
                raise NotFound
            raise Redirect(ctx.get_login_url())

        if (not config['anon']) and (not ctx.user_id):
            raise Redirect(ctx.get_login_url())

        # Try and respond with the result of calling the handler.
        content = handler(ctx, *args, **kwargs)

        for renderer in renderers:
            if ctx.end_pipeline:
                break
            if content is None:
                content = {
                    'content': ''
                }
            elif not isinstance(content, dict):
                content = {
                    'content': content
                    }
            if isinstance(renderer, str):
                content = ctx.render_mako_template(renderer, **content)
            else:
                content = renderer(ctx, **content)

        if content is None:
            content = ''
        elif isinstance(content, unicode):
            content = content.encode('utf-8')
        elif not isinstance(content, str):
            content = str(content)

        if ctx.after_runners:
            for func in ctx.after_runners:
                func(ctx)

        cache = config['cache']
        if cache and http_method != 'POST':
            cache, duration = cache
            etag = md5(content).hexdigest()
            if cache == 'public':
                ctx.cache_response(etag, duration)
            elif cache == 'private':
                ctx.cache_private_response(etag, duration)
            else:
                ctx.do_not_cache_response()

        raise HTTPContent(content)

    # Return the content.
    except HTTPContent, payload:

        content = payload.content
        if 'Content-Type' not in ctx.response_headers:
            ctx.response_headers['Content-Type'] = 'text/html; charset=utf-8'

        ctx.response_headers['Content-Length'] = str(len(content))

        start_response(('%d %s\r\n' % ctx._status), get_response_headers())
        if http_method == 'HEAD':
            return []

        return [content]

    # Handle 404s.
    except NotFound:
        start_response(*RESPONSE_404)
        return [ERROR_404]

    # Handle 401s.
    except AuthError:
        start_response(*RESPONSE_401)
        return [ERROR_401]

    # Handle HTTP 301/302 redirects.
    except Redirect, redirect:
        if 'Content-Type' not in ctx.response_headers:
            ctx.response_headers['Content-Type'] = 'text/html; charset=utf-8'
        headers = get_response_headers()
        if not headers:
            headers = []
        headers.append(("Location", redirect.uri))
        if redirect.permanent:
            start_response(STATUS_301, headers)
        else:
            start_response(STATUS_302, headers)
        return []

    # Handle other HTTP response codes.
    except HTTPError, error:
        start_response(("%s %s" % (error.code, HTTP_STATUS_MESSAGES[error.code])), [])
        return []

    except CapabilityDisabledError:
        start_response(*RESPONSE_503)
        return [ERROR_503]

    # Log any errors and return an HTTP 500 response.
    except Exception, error:
        template_tb = reqlocal.template_error_traceback
        logging.critical(''.join(format_exception(*sys.exc_info())))
        if DEBUG:
            traceback = ''.join(html_format_exception())
        else:
            traceback = ''
        if template_tb:
            logging.critical(PlainErrorTemplate.render(traceback=template_tb))
            if DEBUG:
                traceback = HTMLErrorTemplate.render(traceback=template_tb)
        response = ERROR_500_TRACEBACK % traceback
        start_response(*RESPONSE_500)
        if isinstance(response, unicode):
            response = response.encode('utf-8')
        return [response]

handle_http_request.router = None

# ------------------------------------------------------------------------------
# Template Error Handling
# ------------------------------------------------------------------------------

PlainErrorTemplate = MakoTemplate("""
Traceback (most recent call last):
% for (filename, lineno, function, line) in traceback.traceback:
  File "${filename}", line ${lineno}, in ${function or '?'}
    ${line | trim}
% endfor
${traceback.errorname}: ${traceback.message}
""")

HTMLErrorTemplate = MakoTemplate(r"""
<style type="text/css">
    .stacktrace { margin:5px 5px 5px 5px; }
    .highlight { padding:0px 10px 0px 10px; background-color:#9F9FDF; }
    .nonhighlight { padding:0px; background-color:#DFDFDF; }
    .sample { padding:10px; margin:10px 10px 10px 10px; font-family:monospace; }
    .sampleline { padding:0px 10px 0px 10px; }
    .sourceline { margin:5px 5px 10px 5px; font-family:monospace;}
    .location { font-size:80%; }
</style>
<%
    src = traceback.source
    line = traceback.lineno
    if src:
        lines = src.split('\n')
    else:
        lines = None
%>
<h3>${traceback.errorname}: ${traceback.message}</h3>

% if lines:
    <div class="sample">
    <div class="nonhighlight">
% for index in range(max(0, line-4),min(len(lines), line+5)):
    % if index + 1 == line:
<div class="highlight">${index + 1} ${lines[index] | h}</div>
    % else:
<div class="sampleline">${index + 1} ${lines[index] | h}</div>
    % endif
% endfor
    </div>
    </div>
% endif

<div class="stacktrace"><ul>
% for (filename, lineno, function, line) in traceback.traceback:
    <li>
    <div class="location">${filename}, line ${lineno}:</div>
    <div class="sourceline">${line | h}</div>
    </li>
% endfor
</ul></div>
""")

def template_error_handler(context, error):
    reqlocal.template_error_traceback = RichTraceback()

handle_http_request.template_error_handler = template_error_handler

# ------------------------------------------------------------------------------
# Monkey Patches
# ------------------------------------------------------------------------------

# The ``mako`` templating system uses ``beaker`` to cache segments and this
# needs various patches to make appropriate use of Memcache as a cache backend
# on App Engine.
#
# First, the App Engine memcache client needs to be setup as the ``memcache``
# module.
import google.appengine.api.memcache as memcache

sys.modules['memcache'] = memcache

import beaker.container
import beaker.ext.memcached

# And then the beaker ``Value`` object itself needs to be patched.
class Value(beaker.container.Value):

    def get_value(self):
        stored, expired, value = self._get_value()
        if not self._is_expired(stored, expired):
            return value

        if not self.createfunc:
            raise KeyError(self.key)

        v = self.createfunc()
        self.set_value(v)
        return v

beaker.container.Value = Value
beaker.ext.memcached.verify_directory = lambda x: None

# ------------------------------------------------------------------------------
# Mako
# ------------------------------------------------------------------------------

def call_template_error_handler(*args, **kwargs):
    return handle_http_request.template_error_handler(*args, **kwargs)

# The ``mako`` templating system is used. It offers a reasonably flexible engine
# with pretty decent performance.
class MakoTemplateLookup(object):

    default_template_args = {
        'format_exceptions': False,
        'error_handler': call_template_error_handler,
        'disable_unicode': False,
        'output_encoding': 'utf-8',
        'encoding_errors': 'strict',
        'input_encoding': 'utf-8',
        'module_directory': None,
        'cache_type': 'memcached',
        'cache_dir': '.',
        'cache_url': 'memcached://',
        'cache_enabled': True,
        'default_filters': ['decode.utf8'],  # will be shared across instances
        'buffer_filters': [],
        'imports': None,
        'preprocessor': None
        }

    templates_directory = 'template'

    def __init__(self, **kwargs):
        self.template_args = self.default_template_args.copy()
        self.template_args.update(kwargs)
        self._template_cache = {}
        self._template_mtime_data = {}

    if DEBUG:

        def get_template(self, uri, kwargs=None):

            filepath = join(self.templates_directory, uri + '.mako')
            if not exists(filepath):
                raise IOError("Cannot find template %s.mako" % uri)

            template_time = getmtime(filepath)

            if ((template_time <= self._template_mtime_data.get(uri, 0)) and
                ((uri, kwargs) in self._template_cache)):
                return self._template_cache[(uri, kwargs)]

            if kwargs:
                _template_args = self.template_args.copy()
                _template_args.update(dict(kwargs))
            else:
                _template_args = self.template_args

            template = MakoTemplate(
                uri=uri, filename=filepath, lookup=self, **_template_args
                )

            self._template_cache[(uri, kwargs)] = template
            self._template_mtime_data[uri] = template_time

            return template

    else:

        def get_template(self, uri, kwargs=None):

            if (uri, kwargs) in self._template_cache:
                return self._template_cache[(uri, kwargs)]

            filepath = join(self.templates_directory, uri + '.mako')
            if not exists(filepath):
                raise IOError("Cannot find template %s.mako" % uri)

            if kwargs:
                _template_args = self.template_args.copy()
                _template_args.update(dict(kwargs))
            else:
                _template_args = self.template_args

            template = MakoTemplate(
                uri=uri, filename=filepath, lookup=self, **_template_args
                )

            return self._template_cache.setdefault((uri, kwargs), template)

    def adjust_uri(self, uri, relativeto):
        return uri

def get_mako_template(ctx, uri, kwargs=None, lookup=MakoTemplateLookup().get_template):
    return lookup(uri, kwargs)

def call_mako_template(ctx, template, **kwargs):
    return template.render_unicode(
        ctx=ctx, STATIC=STATIC, **kwargs
        )

def render_mako_template(ctx, template_name, **kwargs):
    ctx.current_template = template_name
    return ctx.get_mako_template(template_name).render_unicode(
        ctx=ctx, STATIC=STATIC, **kwargs
        )

Context.get_mako_template = get_mako_template
Context.call_mako_template = call_mako_template
Context.render_mako_template = render_mako_template

# ------------------------------------------------------------------------------
# HTML Escape
# ------------------------------------------------------------------------------

def escape(s):
    return s.replace(u"&", u"&amp;").replace(u"<", u"&lt;").replace(
        u">", u"&gt;").replace(u'"', u"&quot;")

# ------------------------------------------------------------------------------
# WSGI App Alias
# ------------------------------------------------------------------------------

app = handle_http_request

# ------------------------------------------------------------------------------
# Suppress Warnings
# ------------------------------------------------------------------------------

_ = WebObRequest