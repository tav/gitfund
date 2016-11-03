# Public Domain (-) 2009-2016 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

"""
Twitter API Client for Google App Engine.

The client supports both cases where:

1. You already have an access token and secret for a user.

2. Or you only have the consumer key and secret for your app
   and need to get a user to authorize an access token.

To start, let's look at the first case. Initialise a client
with the various keys and secrets, e.g.

    >>> client = Client(
    ...     consumer_key, consumer_secret,
    ...     access_token, access_token_secret
    ...     )

You can then make API calls by using dot notation for the
path segments of the API URL and keyword arguments for the
parameters, e.g.

    >>> client.statuses.show(id=123, trim_user='true')

    >>> client.statuses.update(status="Hello world!")

    >>> client.friendships.lookup(screen_name="tav")

The returned objects for these calls are the deserialized
versions of the JSON response that Twitter sends back.

----------
Exceptions
----------

If you had exceeded Twitter's rate limits for your API call,
then a ``RateLimitExceeded`` exception will be thrown. It
exposes the ``limit`` and ``reset_time`` (in Unix time) as
attributes so you can appropriately retry later should you
want to.

Similarly if Twitter had not responded with a 200 HTTP
status code, a ``RequestError`` exception will be thrown.
You can access the raw ``urlfetch.Response`` through the
``resp`` attribute of this object.

-------------
Raw Responses
-------------

If you would prefer to not automatically decode the JSON
when making API calls and handle exceptional cases yourself,
then you can specify ``raw_response=True`` to have the raw
``urlfetch.Response`` objects returned, e.g.

    >>> resp = client.statuses.home_timeline(raw_response=True)

    >>> resp
    <urlfetch.Response ...>

To mimic the default behaviour, you can call ``decode_json``
with the response object, i.e.

    >>> decode_json(resp) == client.statuses.home_timeline()
    True

--------------
Async Requests
--------------

App Engine supports asynchronous ``urlfetch`` requests. If
you would like the API calls to be made asynchronously,
specify ``return_rpc=True`` when making specific API calls,
e.g.

    >>> rpc = client.statuses.home_timeline(return_rpc=True)

This returns an ``RPC`` object and initiates the request in
the background. You can then call the ``get_result()``
method on the ``RPC`` object to get the response object.
And, again, you can use ``decode_json`` to mimic the default
behaviour, e.g.

    >>> decode_json(rpc.get_result())

---------
User Auth
---------

If you don't yet have an access token for a user, you need
to first instantiate a client with just the consumer key and
secret for your app, e.g.

    >>> client = Client(consumer_key, consumer_secret)

You then need to get a request token from Twitter by calling
the ``get_request_token`` method:

    >>> req_tok_info = client.get_request_token(
    ...     "https://www.yourapp.com/callback-url"
    ...     )

This returns a dictionary object like:

    >>> req_tok_info
    {'oauth_token': '...', 'oauth_token_secret': '...',
     'oauth_callback_confirmed': '...'}

You can then save the secret somewhere and redirect the user
to Twitter's authentication or authorization URL with the
token as parameter, e.g. assuming your framework provides
``redirect(url)`` and ``db.set(key, value)`` functions:

    >>> req_token = req_tok_info['oauth_token']
    >>> req_token_secret = req_tok_info['oauth_token_secret']
    >>> db.set(req_token, req_token_secret)
    >>> redirect(
    ...     client.authorize_url + "?oauth_token=" + req_tok
    ...     )

Then, assuming that the user approved your app, Twitter
would redirect back to your callback URL with
``oauth_token`` and ``oauth_verifier`` query parameters (or
a ``denied`` parameter if the user hadn't approved).

You can then use the token to retrieve the corresponding
secret, e.g. assuming your framework has ``url.get(param)``
function for getting URL query parameters for the request
and a ``db.get(key)`` function for retrieving stored items
from the datastore:

    >>> req_token = url.get('oauth_token')
    >>> req_token_secret = db.get(req_token)
    >>> req_token_verifier = url.get('oauth_verifier')

Finally, you can ask Twitter to exchange the request token
for an access token with the ``get_access_token`` method:

    >>> access_token_info = client.get_access_token(
    ...     req_token, req_token_secret, req_token_verifier
    ...     )

And assuming everything went well, this should return a
dictionary like:

    >>> access_tok_info
    {'oauth_token': '...', 'oauth_token_secret': '...',
     'user_id': '...', 'screen_name': '...'}

You can then save this info somewhere:

    >>> access_tok = access_tok_info['oauth_token']
    >>> access_tok_secret = access_tok_info['oauth_token_secret']

And create a "subclient" with the auth info, e.g.

    >>> subclient = client.for_auth(access_tok, access_tok_secret)

And use the subclient as you would a normal client, e.g.

    >>> subclient.friendships.lookup(screen_name="tav")
    [{"name": "tav", "id_str": ...}]

----------------------
Configurable Internals
----------------------

Some internals are exposed for your convenience. By default,
all requests time out after 20 seconds. You can modify this
by setting the ``deadline`` attribute on a ``client``:

    >>> client.deadline = 40

Or if you wanted to modify the deadline globally for all
clients:

    >>> Client.deadline = 40

Do bear in mind that App Engine limits urlfetch requests to
a maximum of 60 seconds within frontend requests and to 10
minutes for cron and taskqueue requests.

You can also access the attributes ``authenticate_url`` and
``authorize_url`` in order to send users to the appropriate
auth URL on Twitter, e.g.

    >>> url = client.authorize_url + "?oauth_token=" + token

These attributes are also writable. So you can modify them
should you wish to use an alternative endpoint of some kind.

"""

import logging

from binascii import hexlify
from hashlib import sha1
from hmac import new as hmac
from json import loads
from os import urandom
from time import time
from urllib import quote as urlquote, urlencode

from google.appengine.api.urlfetch import (
    GET, POST, create_rpc, fetch, make_fetch_call
    )

# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class RateLimitExceeded(Exception):
    """Rate Limit reached when making a Twitter API call."""

    def __init__(self, limit, reset_time):
        self.limit = limit
        self.reset_time = reset_time

class RequestError(Exception):
    """Error making a Twitter API call."""

    def __init__(self, resp):
        self.resp = resp

# -----------------------------------------------------------------------------
# Serialisation Utilities
# -----------------------------------------------------------------------------

def encode(param):
    if isinstance(param, unicode):
        param = param.encode('utf-8')
    else:
        param = str(param)
    return urlquote(param, '')

def decode_json(resp):
    if resp.status_code != 200:
        if resp.status_code == 429:
            get = resp.headers.get
            logging.warn("twitter: rate limit exceeded")
            raise RateLimitExceeded(
                int(get('X-Rate-Limit-Limit', 0)),
                int(get('X-Rate-Limit-Reset', 0)),
                )
        logging.error("twitter: %d\n%s" % (resp.status_code, resp.content))
        raise RequestError(resp)
    return loads(resp.content)

# -----------------------------------------------------------------------------
# API Client
# -----------------------------------------------------------------------------

class Client(object):
    """A client for the Twitter API."""

    deadline = 20.0

    api_base_url = "https://api.twitter.com/1.1/"
    access_token_url = "https://api.twitter.com/oauth/access_token"
    authenticate_url = "https://api.twitter.com/oauth/authenticate"
    authorize_url = "https://api.twitter.com/oauth/authorize"
    request_token_url = "https://api.twitter.com/oauth/request_token"

    post_methods = frozenset([
        'account/remove_profile_banner',
        'account/settings',
        'account/update_delivery_device',
        'account/update_profile',
        'account/update_profile_background_image',
        'account/update_profile_banner',
        'account/update_profile_colors',
        'account/update_profile_image',
        'blocks/create',
        'blocks/destroy',
        'direct_messages/destroy',
        'direct_messages/new',
        'favorites/create',
        'favorites/destroy',
        'friendships/create',
        'friendships/destroy',
        'friendships/update',
        'geo/place',
        'lists/create',
        'lists/destroy',
        'lists/members/create',
        'lists/members/create_all',
        'lists/members/destroy',
        'lists/members/destroy_all',
        'lists/subscribers/create',
        'lists/subscribers/destroy',
        'lists/update',
        'saved_searches/create',
        'saved_searches/destroy',
        'statuses/destroy',
        'statuses/filter',
        'statuses/update_with_media',
        'users/report_spam'
        ])

    def __init__(
        self, consumer_key, consumer_secret, oauth_token=None,
        oauth_secret=None
        ):
        self._key = consumer_key
        self._secret = consumer_secret
        self._oauth_token = oauth_token
        self._oauth_secret = oauth_secret

    def __getattr__(self, attr):
        return Proxy(self, attr)

    def __call__(self, path, raw_response=False, return_rpc=False, **kwargs):
        return self._call_explicitly(
            path, self._oauth_token, self._oauth_secret,
            raw_response=raw_response, return_rpc=return_rpc, **kwargs
            )

    def _call_explicitly(
        self, path, oauth_token=None, oauth_secret=None, oauth_callback=None,
        is_post=False, raw_response=False, return_rpc=False, **kwargs
        ):

        params = {
            'oauth_consumer_key': self._key,
            'oauth_nonce': hexlify(urandom(18)),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time())),
            'oauth_version': '1.0'
        }

        key = self._secret + '&'
        if oauth_token:
            params['oauth_token'] = oauth_token
            key += encode(oauth_secret)
        elif oauth_callback:
            params['oauth_callback'] = oauth_callback

        params.update(kwargs)

        if not (path.startswith('https://') or path.startswith('http://')):
            path = self.api_base_url + path + ".json"

        if not is_post:
            is_post = path in self.post_methods
            if not is_post:
                spath = path.split('/')
                npath = ''
                while spath:
                    if npath:
                        npath += '/' + spath.pop(0)
                    else:
                        npath = spath.pop(0)
                    if npath in self.post_methods:
                        is_post = True
                        break

        if is_post:
            meth = POST
            meth_str = 'POST'
        else:
            meth = GET
            meth_str = 'GET'

        message = '&'.join([
            meth_str, encode(path), encode('&'.join(
                '%s=%s' % (k, encode(params[k])) for k in sorted(params)
                ))
            ])

        params['oauth_signature'] = hmac(
            key, message, sha1
            ).digest().encode('base64')[:-1]

        auth = ', '.join(
            '%s="%s"' % (k, encode(params[k])) for k in sorted(params)
            if k not in kwargs
            )

        headers = {'Authorization': 'OAuth %s' % auth}
        if is_post:
            payload = urlencode(kwargs)
        else:
            path += '?' + urlencode(kwargs)
            payload = None

        if return_rpc:
            rpc = create_rpc(self.deadline)
            make_fetch_call(
                rpc, path, payload, meth, headers, validate_certificate=True
                )
            return rpc

        resp = fetch(
            path, payload, meth, headers, deadline=self.deadline,
            validate_certificate=True
            )

        if raw_response:
            return resp

        return decode_json(resp)

    def get_access_token(self, oauth_token, oauth_secret, oauth_verifier):
        resp = self._call_explicitly(
            self.access_token_url, oauth_token, oauth_secret, is_post=True,
            oauth_verifier=oauth_verifier, raw_response=True
            )
        if resp.status_code != 200:
            logging.error("twitter: %d\n%s" % (resp.status_code, resp.content))
            raise RequestError(resp)
        return dict(tuple(param.split('=')) for param in resp.content.split('&'))

    def get_request_token(self, oauth_callback):
        resp = self._call_explicitly(
            self.request_token_url, oauth_callback=oauth_callback,
            is_post=True, raw_response=True
            )
        if resp.status_code != 200:
            logging.error("twitter: %d\n%s" % (resp.status_code, resp.content))
            raise RequestError(resp)
        return dict(tuple(param.split('=')) for param in resp.content.split('&'))

    def for_auth(self, token, secret):
        return Client(self._key, self._secret, token, secret)

class Proxy(object):
    """Access Twitter API methods via dot.notation attribute access."""

    __slots__ = ('_client', '_path')

    def __init__(self, client, path):
        self._client = client
        self._path = path

    def __getattr__(self, attr):
        return Proxy(self._client, self._path + '/' + attr)

    def __call__(self, **kwargs):
        return self._client(self._path, **kwargs)
