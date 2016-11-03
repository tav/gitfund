# Public Domain (-) 2015-2016 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

"""GitHub API Client for Google App Engine."""

import logging

from json import dumps, loads
from urllib import urlencode

from google.appengine.api.urlfetch import (
    DELETE, GET, HEAD, PATCH, POST, PUT, create_rpc, fetch, make_fetch_call
    )

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

JSON = {'Accept': 'application/json', 'Content-Type': 'application/json'}

# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class RateLimitExceeded(Exception):
    """Rate Limit reached when making a GitHub API call."""

    def __init__(self, limit, reset_time):
        self.limit = limit
        self.reset_time = reset_time

class RequestError(Exception):
    """Error making a GitHub API call."""

    def __init__(self, resp):
        self.resp = resp

# -----------------------------------------------------------------------------
# API Client
# -----------------------------------------------------------------------------

class Client(object):
    """A client for the GitHub API."""

    deadline = 20.0

    api_base_url = "https://api.github.com/"
    access_token_url = "https://github.com/login/oauth/access_token"
    authorize_url = "https://github.com/login/oauth/authorize"

    def __init__(self, caller_id, client_id, client_secret, access_token=None):
        self._caller = caller_id
        self._id = client_id
        self._secret = client_secret
        self._token = access_token

    def __getattr__(self, attr):
        return Proxy(self, attr)

    def __call__(
        self, method, path, headers=None, paginated=False, raw_response=False,
        return_rpc=False, **kwargs
        ):

        hdrs = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': self._caller
            }

        if self._token:
            hdrs['Authorization'] = 'token %s' % self._token

        if not path.startswith('https://'):
            path = self.api_base_url + path

        payload = None
        if kwargs:
            if method == GET:
                path = "%s?%s" % (path, urlencode(kwargs))
            else:
                payload = dumps(kwargs)
                hdrs['Content-Type'] = 'application/json'

        if headers:
            hdrs.update(headers)

        if return_rpc:
            rpc = create_rpc(self.deadline)
            make_fetch_call(
                rpc, path, payload, method, hdrs, validate_certificate=True
                )
            return rpc

        resp = fetch(
            path, payload, method, hdrs, deadline=self.deadline,
            validate_certificate=True
            )

        if raw_response:
            return resp

        if resp.status_code != 200:
            if resp.status_code == 403:
                get = resp.headers.get
                lim = int(get('X-RateLimit-Limit', 0))
                rem = int(get('X-RateLimit-Remaining', 0))
                if lim and not rem:
                    logging.warn("github: rate limit exceeded")
                    raise RateLimitExceeded(lim, int(get('X-RateLimit-Reset', 0)))
            logging.error("github: %d\n%s" % (resp.status_code, resp.content))
            raise RequestError(resp)

        data = loads(resp.content)
        if paginated:
            return Paginated(self, resp, data)
        return data

    def get_access_token(self, code, headers=JSON):
        payload = {
            'client_id': self._id,
            'client_secret': self._secret,
            'code': code
        }
        payload = dumps(payload)
        resp = fetch(
            self.access_token_url, payload, POST, headers,
            deadline=self.deadline, validate_certificate=True
            )
        if resp.status_code != 200:
            logging.error("github: %d\n%s" % (resp.status_code, resp.content))
            raise RequestError(resp)
        return loads(resp.content)

    def for_auth(self, token):
        return Client(self._caller, self._id, self._secret, token)

    def moondragon(self):
        return {'Accept': 'application/vnd.github.moondragon+json'}

class Proxy(object):
    """Access GitHub API methods via dot.notation attribute access."""

    __slots__ = ('_client', '_path')

    def __init__(self, client, path):
        self._client = client
        self._path = path

    def __getattr__(self, attr):
        return Proxy(self._client, self._path + '/' + attr)

    def __call__(self, *args):
        return Proxy(self._client, self._path + '/' + '/'.join(args))

    def delete(self, **kwargs):
        return self._client(DELETE, self._path, **kwargs)

    def get(self, **kwargs):
        return self._client(GET, self._path, **kwargs)

    def head(self, **kwargs):
        return self._client(HEAD, self._path, **kwargs)

    def patch(self, **kwargs):
        return self._client(PATCH, self._path, **kwargs)

    def post(self, **kwargs):
        return self._client(POST, self._path, **kwargs)

    def put(self, **kwargs):
        return self._client(PUT, self._path, **kwargs)

class Paginated(object):
    """Pagination wrapper for GitHub API calls."""

    def __init__(self, client, resp, data):
        links = {}
        for part in resp.headers.get('Link', '').split(','):
            part = part.strip()
            if not part:
                continue
            url, rel = part.split('; ')
            url = url[1:-1]
            rel = rel.split('"')[1]
            links[rel] = url
        self.client = client
        self.data = data
        self.links = links

    def rel(self, type):
        if type not in self.links:
            return
        return self.client(GET, self.links[type], paginated=True)
