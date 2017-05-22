# -*- coding: utf-8 -*-

# Public Domain (-) 2015-2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

import logging
import re

from base64 import b32encode, b64encode, urlsafe_b64encode
from cgi import escape
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from hashlib import sha256
from hmac import HMAC
from json import dumps as encode_json, loads as decode_json
from random import choice
from struct import pack
from thread import allocate_lock
from threading import local
from time import time
from urllib import urlencode

from config import (
    ADMIN_AUTH_KEY, CAMPAIGN_DESCRIPTION, CAMPAIGN_GOALS,  CAMPAIGN_TEAM,
    CAMPAIGN_TITLE, CANONICAL_HOST, FANOUT_KEY, FANOUT_REALM, GCS_BUCKET,
    GITHUB_ACCESS_TOKEN, GITHUB_CALLER_ID, GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET, HMAC_KEY, LIVE, MAILJET_API_KEY, MAILJET_SECRET_KEY,
    MAILJET_SENDER_EMAIL, MAILJET_SENDER_NAME, ON_GOOGLE,
    OPEN_EXCHANGE_RATES_APP_ID, PAGES, PLAN_DESCRIPTIONS, SLACK_TOKEN,
    STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_TOKEN,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET
    )

from model import (
    BillingInfo, CountryProof, CronStatus, ExchangeRates, GitHubProfile,
    GitHubRepo, Login, SponsorRecord, SponsorTotals, StripeEvent,
    TransactionRecord, TwitterProfile, User
    )

from weblite import (
    app, Context, handle, NotFound, Redirect
    )

import cloudstorage as gcs
import stripe

from emoji import EMOJI_MAP, EMOJI_SHORTCODES
from finance import BASE_PRICES, PLAN_FACTORS, PLAN_SLOTS
from gfm import (
    AutolinkExtension, AutomailExtension, SpacedLinkExtension,
    StrikethroughExtension
    )

from github import Client as GithubClient

from google.appengine.api.images import Image, JPEG, PNG
from google.appengine.api.memcache import (
    delete as delete_cache, delete_multi as delete_cache_multi,
    flush_all, get as get_cache, get_multi as get_cache_multi,
    set as set_cache, set_multi as set_cache_multi
    )

from google.appengine.api.urlfetch import fetch as urlfetch, POST
from google.appengine.ext import db
from google.appengine.ext.db import run_in_transaction

from markdown import Extension, Markdown
from markdown.extensions.abbr import AbbrExtension
from markdown.extensions.attr_list import AttrListExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.footnotes import FootnoteExtension
from markdown.extensions.smart_strong import SmartEmphasisExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from markdown.preprocessors import Preprocessor

from tavutil.crypto import (
    create_tamper_proof_string, secure_string_comparison,
    validate_tamper_proof_string
    )

from territories import TERRITORIES, TERRITORY_EXCEPTIONS
from twitter import Client as TwitterClient

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

AUTH_HANDLERS = frozenset([
    'cancel.sponsorship',
    'manage.sponsorship',
    'update.billing.details',
    'update.sponsor.profile',
    'view.billing.history',
])

CACHE_SPECS = {}

GITHUB_MEMCACHE_KEYS = ['github.repo|gitfund']
GITHUB_PROFILES = []
SOCIAL_MEMCACHE_KEYS = GITHUB_MEMCACHE_KEYS[:]
TWITTER_MEMCACHE_KEYS = []
TWITTER_PROFILES = []

README_PNG = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x05\x00\x00\x00\x96\x04\x03\x00\x00\x00\xe4\xb3_;\x00\x00\x00\x0fPLTE\xcc\xcc\xcc\xd2\xd2\xd2\xd6\xd6\xd6\xd9\xd9\xd9\xea\xea\xea\x98zvV\x00\x00\x00\x19IDAT(Scp\x16v`P\x00\xc2Q0\n\xa8\x01@i\t\x98\xa6\x00\xf7\xfd\x01\xad\xc4e\xf0\\\x00\x00\x00\x00IEND\xaeB`\x82'

SIMG = "By Markus Spiske: https://unsplash.com/@markusspiske?photo=xekxE_VR0Ec"

VALID_SPONSOR_IMAGE_CONTENT_TYPES = frozenset([
    'image/jpeg',
    'image/png',
])

# -----------------------------------------------------------------------------
# Gravatar URL
# -----------------------------------------------------------------------------

GRAVATAR_PREFIX = '//www.gravatar.com/avatar/'
GRAVATAR_SUFFIX = '?d=https%3A%2F%2F' + CANONICAL_HOST + '%2Fprofile.png'

# -----------------------------------------------------------------------------
# Stripe API Config
# -----------------------------------------------------------------------------

stripe.api_key = STRIPE_SECRET_KEY

# -----------------------------------------------------------------------------
# Context Extensions
# -----------------------------------------------------------------------------

_marker = object()

def current_year():
    return datetime.utcnow().year

def get_site_sponsors():
    sponsors = get_local('sponsors')
    profiles = []
    for tier in ['platinum', 'gold', 'silver', 'bronze']:
        tier_sponsors = sponsors[tier]
        if tier_sponsors:
            profiles.append(choice(tier_sponsors))
    return profiles

def get_sponsor_image_url(info, size=None):
    typ, val = info['img']
    if typ == 'b':
        if size:
            return '/sponsor.image/' + val + '/' + size
        return '/sponsor.image/' + val
    if typ == 'g':
        if size:
            return GRAVATAR_PREFIX + val + GRAVATAR_SUFFIX + '&s=' + size
        return GRAVATAR_PREFIX + val + GRAVATAR_SUFFIX

def linkify_github_bio(text):
    return replace_github_usernames(create_github_profile_link, escape(text))

def linkify_twitter_bio(text):
    return replace_twitter_usernames(create_twitter_profile_link, escape(text))

def log(ctx, name, data=_marker):
    if data is _marker:
        data = name
        name = ctx.name
    logging.info("#%s %s" % (name, encode_json(data)))

def pluralise(label, count):
    if count == 1:
        return label
    return label + 's'

Context.STRIPE_PUBLISHABLE_KEY = STRIPE_PUBLISHABLE_KEY
Context.current_year = staticmethod(current_year)
Context.get_site_sponsors = staticmethod(get_site_sponsors)
Context.get_sponsor_image_url = staticmethod(get_sponsor_image_url)
Context.linkify_github_bio = staticmethod(linkify_github_bio)
Context.linkify_twitter_bio = staticmethod(linkify_twitter_bio)
Context.log = log
Context.noindex = False
Context.page_title = ''
Context.preview_mode = False
Context.pluralise = staticmethod(pluralise)
Context.show_sponsors_footer = True
Context.site_image = ''
Context.site_description = ''
Context.site_title = ''
Context.stripe_js = False

# -----------------------------------------------------------------------------
# Local Cache
# -----------------------------------------------------------------------------

class CacheSpec(object):
    def __init__(self, duration, generator):
        self.duration = duration
        self.generator = generator
        self.lock = allocate_lock()
        self.timestamp = 0
        self.value = None

def get_local(ident, force=False):
    spec, now = CACHE_SPECS[ident], time()
    lock = spec.lock
    lock.acquire()
    val = spec.value
    if force or ((now - spec.timestamp) > spec.duration):
        lock.release()
        val = spec.generator()
        lock.acquire()
        spec.timestamp = now
        spec.value = val
    lock.release()
    return val

# -----------------------------------------------------------------------------
# Local Cache Generator Functions
# -----------------------------------------------------------------------------

def get_social_profiles():
    cache = get_cache_multi(SOCIAL_MEMCACHE_KEYS)
    github = {}
    repo = None
    twitter = {}
    to_get = []; get = to_get.append
    for username in GITHUB_PROFILES:
        key = 'github|%s' % username
        if key in cache:
            github[username] = cache[key]
        else:
            get(create_key(GitHubProfile.kind(), username))
    if cache.get('github.repo|gitfund'):
        repo = cache['github.repo|gitfund']
    else:
        get(create_key(GitHubRepo.kind(), 'gitfund'))
    for username in TWITTER_PROFILES:
        key = 'twitter|%s' % username
        if key in cache:
            twitter[username] = cache[key]
        else:
            get(create_key(TwitterProfile.kind(), username))
    if to_get:
        entries = {}
        resp = db.get(to_get)
        for idx, entity in enumerate(resp):
            if isinstance(entity, TwitterProfile):
                username = entity.key().name()
                twitter[username] = entity
                entries['twitter|%s' % username] = entity
            elif isinstance(entity, GitHubProfile):
                username = entity.key().name()
                github[username] = entity
                entries['github|%s' % username] = entity
            elif isinstance(entity, GitHubRepo):
                repo = entity
                entries['github.repo|gitfund'] = entity
            else:
                raise ValueError(
                    "Received unexpected entity at %r[%d]: %r"
                    % (resp, idx, entity)
                    )
        set_cache_multi(entries, 300)
    return github, repo, twitter

def get_sponsors():
    sponsors = get_cache('sponsors')
    if sponsors:
        return sponsors
    sponsors = {
        'platinum': [],
        'gold': [],
        'silver': [],
        'bronze': [],
    }
    for sponsor in User.all().filter('sponsor =', True).order(
        'sponsorship_started'
        ).run(batch_size=700):
        sponsors[sponsor.plan].append({
            'img': sponsor.get_image_spec(),
            'text': sponsor.get_link_text(),
            'url': sponsor.link_url,
        })
    set_cache('sponsors', sponsors, 60)
    return sponsors

# -----------------------------------------------------------------------------
# GitHub API Client and Utility Functions
# -----------------------------------------------------------------------------

def create_github_profile_link(m):
    username = m.group(1)[1:]
    return '<a href="https://github.com/%s">@%s</a>' % (username, username)

replace_github_usernames = re.compile(
    '(?<=^|(?<=[^a-zA-Z0-9-\.]))(@[A-Za-z0-9]+)'
    ).sub

github = GithubClient(
    GITHUB_CALLER_ID, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET,
    GITHUB_ACCESS_TOKEN
    )

# -----------------------------------------------------------------------------
# Twitter API Client and Utility Functions
# -----------------------------------------------------------------------------

def create_twitter_profile_link(m):
    username = m.group(1)[1:]
    return '<a href="https://twitter.com/%s">@%s</a>' % (username, username)

replace_twitter_usernames = re.compile(
    '(?<=^|(?<=[^a-zA-Z0-9-_\.]))(@[A-Za-z0-9_]+)'
    ).sub

twitter = TwitterClient(
    TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
    )

# -----------------------------------------------------------------------------
# JWT Support
# -----------------------------------------------------------------------------

def jwt_encode(s):
    return urlsafe_b64encode(s).rstrip('=')

def get_sha256_jwt(issuer, secret, expiration=None):
    # Header is the base64 of {"alg":"HS256","typ":"JWT"}
    header = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
    payload = {'iss': issuer}
    if expiration:
        payload['exp'] = int(time()) + expiration
    payload = jwt_encode(encode_json(payload, separators=(',', ':')))
    signature = jwt_encode(HMAC(secret, header+'.'+payload, sha256).digest())
    return header + '.' + payload + '.' + signature

# -----------------------------------------------------------------------------
# Fanout Support
# -----------------------------------------------------------------------------

FANOUT_API_URL = "https://api.fanout.io/realm/%s/publish/" % FANOUT_REALM

def fanout_publish(channel, data):
    if not ON_GOOGLE:
        logging.info("Skipping publishing to %s: %r" % (channel, data))
        return
    auth = get_sha256_jwt(FANOUT_REALM, FANOUT_KEY, 3600)
    headers = {
        'Authorization': "Bearer %s" % auth,
        'Content-Type': 'application/json'
    }
    payload = encode_json(
        {"items": [{"channel": channel, "json-object": data}]}
        )
    try:
        resp = urlfetch(
            FANOUT_API_URL, payload, POST,
            deadline=30, headers=headers, validate_certificate=True
            )
    except Exception as err:
        logging.error(
            'A Fanout error occurred when publishing to %s: %r' % (channel, err)
            )
        return err
    if resp.status_code != 200:
        logging.error(
            'A Fanout error occurred when publishing to %s (status: %d)' % (
                    channel, resp.status_code
            ))
        return resp

# -----------------------------------------------------------------------------
# Mailjet Extension
# -----------------------------------------------------------------------------

MAILJET_API_URL = 'https://api.mailjet.com/v3/send'
MAILJET_AUTH = b64encode(MAILJET_API_KEY + ':' + MAILJET_SECRET_KEY)
MAILJET_HEADERS = {
    'Authorization': "Basic %s" % MAILJET_AUTH,
    'Content-Type': 'application/json'
}

def send_email(ctx, subject, name, email, template, **kwargs):
    content = ctx.render_mako_template('email.' + template, **kwargs)
    body = ctx.render_mako_template('email', content=content, **kwargs)
    fields = {
        'FromEmail': MAILJET_SENDER_EMAIL,
        'FromName': MAILJET_SENDER_NAME,
        'Recipients': [{'Email': email, 'Name': name}],
        'Subject': subject,
        'Html-part': body
    }
    # if not ON_GOOGLE:
    #     logging.info("Skipping sending of email: %r" % subject)
    #     logging.info("Email body:\n%s\n" % body)
    #     return
    try:
        resp = urlfetch(
            MAILJET_API_URL, encode_json(fields), POST,
            deadline=30, headers=MAILJET_HEADERS, validate_certificate=True
            )
    except Exception as err:
        logging.error(
            'A Mailjet error occurred when sending to %s: %r' % (email, err)
            )
        return err
    if resp.status_code != 200:
        logging.error(
            'A Mailjet error occurred when sending to %s: %r (status: %d)' % (
                    email, resp.content, resp.status_code
            ))
        return resp

Context.send_email = send_email

# -----------------------------------------------------------------------------
# Emoji Support
# -----------------------------------------------------------------------------

class EmojiPreprocessor(Preprocessor):
    def run(self, lines, MAP=EMOJI_MAP, SHORTCODES=EMOJI_SHORTCODES):
        new_lines = []; append = new_lines.append
        for line in lines:
            if line.strip():
                iline = line.encode('utf-8', 'replace')
                for chars, shortcode in MAP:
                    if chars in iline:
                        iline = iline.replace(chars, shortcode)
                if not (':' in iline):
                    append(line)
                    continue
                shortcode = ''
                in_short = None
                nline = []; out = nline.append
                for char in iline:
                    if in_short:
                        if char == ':':
                            if shortcode in SHORTCODES:
                                out(SHORTCODES[shortcode])
                            else:
                                out(':' + shortcode + ':')
                            in_short = None
                            shortcode = ''
                        elif char in 'abcdefghijklmnopqrstuvwxyz0123456789-_+':
                            shortcode += char
                        else:
                            out(':' + shortcode + char)
                            in_short = None
                            shortcode = ''
                    elif char == ':':
                        in_short = 1
                        shortcode = ''
                    else:
                        out(char)
                if in_short:
                    out(':' + shortcode)
                line = ''.join(nline).decode('utf-8')
            append(line)
        return new_lines

class EmojiExtension(Extension):
    """An extension that turns all :emoji: refs and runes into images."""

    def extendMarkdown(self, md, md_globals):
        md.registerExtension(self)
        md.preprocessors.add('emoji', EmojiPreprocessor(md), '_begin')

# -----------------------------------------------------------------------------
# Markdown Renderer
# -----------------------------------------------------------------------------

LOCAL = local()

def render_markdown(text):
    if hasattr(LOCAL, 'md'):
        md = LOCAL.md
        md.reset()
    else:
        md = Markdown(
            extensions=[
                AbbrExtension(),
                AttrListExtension(),
                AutolinkExtension(),
                AutomailExtension(),
                CodeHiliteExtension(
                    css_class='syntax', guess_lang=False, linenums=False
                    ),
                EmojiExtension(),
                FencedCodeExtension(),
                FootnoteExtension(),
                SmartEmphasisExtension(),
                SpacedLinkExtension(),
                StrikethroughExtension(),
                TableExtension(),
                TocExtension()
            ],
            output_format='html5',
            tab_length=2
        )
        LOCAL.md = md
    resp = md.convert(text)
    return resp

# -----------------------------------------------------------------------------
# Google Cloud Storage
# -----------------------------------------------------------------------------

def get_gcs_filename(path):
    return '/gs' + get_gcs_path(path)

def get_gcs_path(path):
    if ON_GOOGLE and LIVE:
        return '/%s/prod/%s' % (GCS_BUCKET, path)
    return '/%s/dev/%s' % (GCS_BUCKET, path)

def get_sponsor_image_data(id, height):
    if height:
        height = int(height)
    if id.count('.') != 1:
        raise ValueError("Invalid image id: %r" % id)
    image_id, fmt = id.split('.')
    if fmt == 'jpeg':
        ctype = 'image/jpeg'
    elif fmt == 'png':
        ctype = 'image/png'
    else:
        raise ValueError("Unsupported image type: %r" % fmt)
    if height:
        img = Image(filename=get_gcs_filename('sponsor.image/' + image_id))
        img.resize(height=height)
        if fmt == 'jpeg':
            data = img.execute_transforms(output_encoding=JPEG, quality=100)
        elif fmt == 'png':
            data = img.execute_transforms(output_encoding=PNG)
    else:
        data = read_file('sponsor.image/' + image_id)
    return image_id, ctype, data

def read_file(path):
    f = gcs.open(get_gcs_path(path), 'r')
    data = f.read()
    f.close()
    return data

def write_file(path, data):
    f = gcs.open(get_gcs_path(path), 'w', options={'x-goog-acl': 'private'})
    f.write(data)
    f.close()

# -----------------------------------------------------------------------------
# Finance-related Utility Functions
# -----------------------------------------------------------------------------

TWO_DECIMAL_PLACES = Decimal('0.01')
FOUR_DECIMAL_PLACES = Decimal('0.0001')

PLAN_PORTIONS = {}

def get_stripe_plan(currency, plan):
    return 'gitfund.%s.%s.v%d' % (
        plan, currency.lower(), len(BASE_PRICES[currency])
    )

def init_plan_info():
    total = 0
    totals = {}
    for plan, factor in PLAN_FACTORS.iteritems():
        totals[plan] = plan_total = Decimal(PLAN_SLOTS[plan] * factor)
        total += plan_total
    check = 0
    for plan, plan_total in totals.iteritems():
        portion = plan_total / total
        PLAN_PORTIONS[plan] = portion / PLAN_SLOTS[plan]
        check += portion
    check *= 100
    if check != 100:
        raise ValueError("Plan portions do not tally to 100%%: %s%%" % check)

# -----------------------------------------------------------------------------
# Other Utility Functions
# -----------------------------------------------------------------------------

create_key = db.Key.from_path

def is_email(email, match_addr=re.compile(r'.+\@.+').match):
    if not match_addr(email):
        return
    if len(email.encode('utf-8')) > 254:
        return
    return True

def gen_js_territory_data(varname, dataset):
    idx = 0
    data = []; append_data = data.append
    output = []; out = output.append
    seen = {}
    for territory in sorted(dataset):
        value = dataset[territory]
        tcode = territory.lower().replace('-', '_')
        if value not in seen:
            append_data(encode_json(value))
            seen[value] = idx
            idx += 1
        out("%s:%d" % (tcode, seen[value]))
    return "%s={%s};%s_DATA=[%s]" % (varname, ','.join(output), varname, ','.join(data))

def get_login_key_name(email):
    return 'e.' + b32encode(email.lower().encode('utf-8')).rstrip('=')

def get_user_from_email(email):
    login = Login.get_by_key_name(get_login_key_name(email))
    if not login:
        return
    if not login.user_id:
        return
    return User.get_by_id(login.user_id)

def read(path):
    f = open(path, 'rb')
    data = f.read().decode('utf-8')
    f.close()
    return data

strptime = datetime.strptime

# -----------------------------------------------------------------------------
# Project Renderer
# -----------------------------------------------------------------------------

def render_project(ctx):
    ctx.site_description = CAMPAIGN_DESCRIPTION
    ctx.site_image = ctx.site_url + ctx.STATIC("gfx/cover.lossy.jpeg")
    ctx.site_image_attribution = SIMG
    ctx.site_title = CAMPAIGN_TITLE
    github_profiles, github_repo, twitter_profiles = get_local('social.profiles')
    total_sponsors, fund_total, plan_totals = get_totals()
    goals = []
    for goal in CAMPAIGN_GOALS:
        if fund_total >= goal.percentage:
            goals.append((goal.percentage, goal.description, True))
        else:
            goals.append((goal.percentage, goal.description, False))
            break
    # plans = [(plan, plan_totals.get(plan.id, 0)) for plan in CAMPAIGN_PLANS]
    raised_percentage = 0
    return dict(
        campaign_content=CAMPAIGN_CONTENT,
        campaign_description=CAMPAIGN_DESCRIPTION,
        campaign_team=CAMPAIGN_TEAM,
        campaign_title=CAMPAIGN_TITLE,
        fund_total=fund_total,
        github_profiles=github_profiles,
        github_repo=github_repo,
        goals=goals,
        plan_slots=PLAN_SLOTS,
        plan_descriptions=PLAN_DESCRIPTIONS,
        raised_percentage=raised_percentage,
        territories=TERRITORIES,
        territory_exceptions=TERRITORY_EXCEPTIONS,
        territory_selected='ES-CN',
        total_sponsors=total_sponsors,
        twitter_profiles=twitter_profiles,
    )

# -----------------------------------------------------------------------------
# Handlers
# -----------------------------------------------------------------------------

@handle('/')
def frontpage(ctx, **kwargs):
    raise Redirect('/tav/gitfund')

@handle(['admin', 'site'])
def admin(ctx, key=None, xsrf=None):
    ctx.page_title = "Admin"
    if ctx.is_admin:
        raise Redirect('/admin.sponsors')
    if key is None:
        return {}
    ctx.validate_xsrf(xsrf)
    if not secure_string_comparison(key, ADMIN_AUTH_KEY):
        logging.warn("Invalid auth attempt.")
        return {
            "error": "Invalid auth key. This failed attempt has been logged for security purposes."
        }
    ctx.set_secure_cookie('admin', ADMIN_AUTH_KEY)
    raise Redirect('/admin.sponsors')

@handle(['admin.sponsors', 'site'])
def admin_sponsors(ctx, cursor=None):
    site.page_title = "Sponsors (Admin View)"

@handle
def auth(ctx, token=None, return_to=None):
    if not token:
        raise NotFound
    if return_to not in AUTH_HANDLERS:
        raise NotFound
    user_id = validate_tamper_proof_string('authtoken', token, HMAC_KEY)
    if not user_id:
        return "<h1>Sorry, this auth link has expired.</h1>"
    ctx.set_secure_cookie('auth', user_id)
    raise Redirect('/' + return_to)

@handle(['cancel.sponsorship', 'site'], anon=False)
def cancel_sponsorship(ctx, confirm=None, xsrf=None):
    ctx.page_title = "Cancel Sponsorship"

@handle(['community', 'site'])
def community(ctx, email=None, xsrf=''):
    ctx.page_title = "Slack/IRC Community"
    if email is None:
        return {}
    ctx.validate_xsrf(xsrf)
    if not is_email(email):
        return {'error': "Please provide a valid email address."}
    payload = urlencode({'token': SLACK_TOKEN, 'email': email})
    try:
        resp = urlfetch(
            "https://slack.com/api/users.admin.invite", payload=payload,
            method=POST, deadline=30, validate_certificate=True
            )
    except Exception as err:
        logging.error(
            "Got unexpected error when trying to invite %r to slack: %r"
            % (email, err)
            )
        return {'error': "Sorry, there was an unexpected error. Please try again later."}
    if resp.status_code != 200:
        logging.error(
            "Got unexpected error code %d when trying to invite %r to slack"
            % (resp.status_code, email)
            )
        return {'error': "Sorry, there was an unexpected error. Please try again later."}
    return {'sent': True}

@handle
def compare_currencies(ctx):
    rates = decode_json(
        ExchangeRates.get_by_key_name('latest').data, parse_float=Decimal
        )['rates']
    data = []
    usd_value = BASE_PRICES['USD'][-1]
    for currency in BASE_PRICES:
        value = Decimal(BASE_PRICES[currency][-1])
        current = rates[currency] * usd_value
        ratio = (value / current).quantize(FOUR_DECIMAL_PLACES, ROUND_HALF_UP)
        data.append((currency, ratio, int(current), value))
    data = sorted(data, key=lambda row: row[1])
    ctx.response_headers['Content-Type'] = 'text/plain'
    return '\n'.join("%s\t\t%s\t\t%s\t\t%s" % row for row in data)

@handle
def cron_fxrates(ctx):
    rates = ExchangeRates.get_or_insert('latest')
    if rates.data and ((datetime.utcnow() - rates.updated) <= timedelta(hours=1)):
        return
    try:
        resp = urlfetch(
            'https://openexchangerates.org/api/latest.json?app_id=%s'
            % OPEN_EXCHANGE_RATES_APP_ID
            )
        if resp.status_code != 200:
            raise ValueError("Got unexpected response code: %d" % resp.status_code)
        data = resp.content
        decode_json(data, parse_float=Decimal)['rates']
        rates.data = data
        rates.put()
        delete_cache('fxrates')
    except Exception, err:
        logging.exception("Couldn't fetch exchange rates: %s" % err)
    return 'OK'

@handle
def cron_github(ctx):
    for username in GITHUB_PROFILES:
        profile = GitHubProfile.get_by_key_name(username)
        if not profile:
            profile = GitHubProfile(key_name=username)
        info = github.users(username).get()
        profile.avatar = info['avatar_url']
        if info['bio']:
            profile.description = info['bio']
        profile.followers = info['followers']
        profile.joined = strptime(info['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        if info['name']:
            profile.name = info['name']
        profile.put()
    repo = GitHubRepo.get_by_key_name('gitfund')
    if not repo:
        repo = GitHubRepo(key_name='gitfund')
    info = github.repos.tav.gitfund.get()
    repo.stars = info['stargazers_count']
    repo.put()
    delete_cache_multi(GITHUB_MEMCACHE_KEYS)
    return 'OK'

@handle
def cron_invoices(ctx):
    return 'OK'

@handle
def cron_sync(ctx, sync_all=False):
    return 'OK'

@handle
def cron_twitter(ctx):
    for screen_name in TWITTER_PROFILES:
        profile = TwitterProfile.get_by_key_name(screen_name)
        if not profile:
            profile = TwitterProfile(key_name=screen_name)
        info = twitter.users.show(screen_name=screen_name, include_entities=False)
        profile.avatar = info['profile_image_url_https']
        profile.description = info['description']
        profile.followers = info['followers_count']
        profile.joined = datetime.strptime(info['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        profile.name = info['name']
        profile.put()
    delete_cache_multi(TWITTER_MEMCACHE_KEYS)
    return 'OK'

@handle(anon=False)
def invoice_pdf(ctx):
    pass

@handle(['login', 'site'])
def login(ctx, return_to='manage.sponsorship', email='', existing=False, xsrf=None):
    ctx.page_title = "Log in to GitFund"
    if return_to not in AUTH_HANDLERS:
        raise NotFound
    if xsrf is None:
        return {'return_to': return_to, 'email': email, 'existing': existing}
    ctx.validate_xsrf(xsrf)
    if not is_email(email):
        return {
            'error': "Please provide a valid email address.",
            'return_to': return_to,
            'email': email
        }
    user = get_user_from_email(email)
    if not user:
        return {
            'error': "Sorry, we couldn't find an account for %s." % email,
            'return_to': return_to,
            'email': email
        }
    user_id = str(user.key().id())
    token = create_tamper_proof_string('authtoken', user_id, HMAC_KEY, 86400)
    authlink = ctx.compute_url('auth', token, return_to)
    intent = return_to.split('.')
    intent_button = ' '.join(part.title() for part in intent)
    err = ctx.send_email(
        intent_button, user.name, user.email, 'authlink',
        authlink=authlink, intent=intent, intent_button=intent_button
        )
    if err:
        return {
            'error': "Sorry, there was an error emailing %s." % email,
            'return_to': return_to,
            'email': email
        }
    return {'sent': True}

@handle
def logout(ctx):
    ctx.expire_cookie('auth')
    ctx.expire_cookie('admin')
    raise Redirect('/')

@handle(['manage.sponsorship', 'site'], anon=False)
def manage_sponsorship(ctx):
    ctx.page_title = "Manage Sponsorship"

@handle
def readme_image(ctx, plan=None, size='300'):
    if plan not in PLAN_SLOTS:
        raise NotFound
    try:
        int(size)
    except:
        raise NotFound
    sponsors = get_local('sponsors')[plan]
    if not sponsors:
        ctx.response_headers['Cache-Control'] = 'public, max-age=30;'
        ctx.response_headers['Content-Type'] = 'image/png'
        return README_PNG
    sponsor = choice(sponsors)
    img = sponsor['img']
    if img[0] == 'b':
        try:
            image_id, ctype, data = get_sponsor_image_data(img[1], size)
        except:
            raise NotFound
        ctx.response_headers['Cache-Control'] = 'public, max-age=30;'
        ctx.response_headers['Content-Type'] = ctype
        return data
    gravatar_url = 'https:' + get_sponsor_image_url(sponsor, size)
    resp = urlfetch(gravatar_url, validate_certificate=True)
    if resp.status_code != 200:
        raise NotFound
    ctype = resp.headers.get('Content-Type')
    if ctype not in VALID_SPONSOR_IMAGE_CONTENT_TYPES:
        raise NotFound
    ctx.response_headers['Cache-Control'] = 'public, max-age=30;'
    ctx.response_headers['Content-Type'] = ctype
    return resp.content

@handle(['page', 'site'])
def site(ctx, page=None, cache={}):
    if page in cache:
        ctx.page_title = PAGES[page]
        return cache[page]
    if not page:
        raise NotFound
    if page not in PAGES:
        raise NotFound
    ctx.page_title = PAGES[page]
    text = read('page/%s.md' % page)
    return cache.setdefault(page, render_markdown(text))

@handle(['site.sponsors', 'site'])
def site_sponsors(ctx, cursor=None):
    ctx.page_title = "Our Sponsors"
    ctx.show_sponsors_footer = False
    return {
        'sponsors': get_local('sponsors')
    }

@handle(['sponsor.gitfund', 'site'])
def sponsor_gitfund(ctx, plan='', name='', email='', card='', xsrf=None):
    ctx.page_title = "Sponsor GitFund!"

@handle
def sponsor_image(ctx, id, height=None):
    try:
        image_id, ctype, data = get_sponsor_image_data(id, height)
    except:
        raise NotFound
    ctx.response_headers['Content-Type'] = ctype
    ctx.cache_response(image_id, 3600)
    return data

@handle
def static_file(ctx, *path):
    raise Redirect(ctx.STATIC('/'.join(path)))

@handle
def stripe_webhook(ctx, token, **kwargs):
    if not secure_string_comparison(token, STRIPE_WEBHOOK_TOKEN):
        raise NotFound
    customer = ''
    if 'data' in kwargs:
        data = kwargs['data']
        if 'object' in data:
            obj = data['object']
            if 'customer' in obj:
                cus = obj['customer']
                if cus:
                    customer = cus
    StripeEvent.get_or_insert(
        kwargs.pop('id'), created=kwargs.pop('created'), customer=customer,
        event_type=kwargs.pop('type'), livemode=kwargs.pop('livemode'),
        data=encode_json(kwargs)
        )
    return 'OK'

@handle(['project', 'site'])
def tav(ctx, project='', **kwargs):
    if project != 'gitfund':
        raise NotFound
    ctx.preview_mode = True
    return render_project(ctx)

@handle(['update.billing.details', 'site'], anon=False)
def update_billing_details(ctx, plan='', name='', card='', xsrf=None):
    ctx.page_title = "Update Billing Details"

@handle(['update.sponsor.profile', 'site'], anon=False)
def update_sponsor_profile(ctx, link_text='', link_url='', image=None, xsrf=None):
    ctx.page_title = "Update Sponsor Profile"
    if xsrf is None:
        return {
            'link_text': ctx.user.get_link_text(),
            'link_url': ctx.user.link_url,
        }
    def error(msg):
        return {
            'error': msg,
            'link_text': link_text,
            'link_url': link_url,
        }
    link_text = link_text.strip()
    if link_text and len(link_text.encode('utf-8')) > 40:
        return error("The link text must be less than 40 bytes long.")
    link_url = link_url.strip()
    if link_url:
        if not (link_url.startswith('http://') or link_url.startswith('https://')):
            return error("The link URL must start with either http:// or https://")
        if len(link_url.encode('utf-8')) > 500:
            return error("The link URL must be less than 500 bytes long.")
    image_id = ''
    if hasattr(image, 'file'):
        data = image.value
        if data and len(data) > (12 << 20):
            return error("The sponsor image must be less than 12MB.")
        if data.startswith('\xff\xd8\xff'):
            fmt = 'jpeg'
        elif data.startswith('\x89PNG\r\n\x1a\n'):
            fmt = 'png'
        else:
            return error("Sorry, only JPEG and PNG images are currently supported.")
        meta = Image(data)
        meta.im_feeling_lucky()
        meta.execute_transforms(
            parse_source_metadata=True, output_encoding=JPEG, quality=1
        )
        width, height = meta.width, meta.height
        if (width < 300) or (height < 150):
            return error("Sorry, the image must be at least 300px wide and 150px high.")
        if (float(width) / height) > 4:
            return error("Sorry, the width of the image cannot be more than 4 times its height.")
        image_id = b32encode(sha256(data).digest() + pack('d', time()))
        write_file('sponsor.image/' + image_id, data)
    def txn():
        user = User.get_by_id(ctx.user_id)
        user.link_text = link_text
        user.link_url = link_url
        if image_id:
            user.image_id = image_id + '.' + fmt
        user.put()
        return user
    ctx.log({
        "image_id": image_id,
        "link_text": link_text,
        "link_url": link_url,
        "user_id": ctx.user_id,
    })
    user = run_in_transaction(txn)
    delete_cache('sponsors')
    return {
        'link_text': user.get_link_text(),
        'link_url': user.link_url,
        'updated': True,
    }

@handle
def validate_vat(ctx):
    pass

@handle(['view.billing.history', 'site'], anon=False)
def view_billing_history(ctx):
    site.page_title = "View Billing History"

# ------------------------------------------------------------------------------
# Dev Handlers
# ------------------------------------------------------------------------------

if not LIVE:

    @handle(admin=True)
    def login_as(ctx, email, plan='gold', name=None):
        login_key = get_login_key_name(email)
        login = Login.get_or_insert(login_key)
        user_id = login.user_id
        if not user_id:
            if not name:
                name = email.split('@')[0]
            user = User(
                email=email, name=name, plan=plan, sponsor=True,
                sponsorship_started=datetime.utcnow()
                )
            user.put()
            def txn(user_id):
                login = Login.get_by_key_name(login_key)
                if login.user_id:
                    return login.user_id
                login.user_id = user_id
                login.put()
                return user_id
            user_id = run_in_transaction(txn, user.key().id())
        ctx.set_secure_cookie('auth', str(user_id))
        raise Redirect('/manage.sponsorship')

    @handle(admin=True)
    def site_bootstrap(ctx):
        cron_fxrates(ctx)
        cron_github(ctx)
        cron_twitter(ctx)
        return 'OK'

    @handle(admin=True)
    def site_flush(ctx):
        flush_all()
        return 'OK'

    @handle(admin=True)
    def site_wipe(ctx):
        for model in [
            BillingInfo, CountryProof, CronStatus, ExchangeRates, GitHubProfile,
            GitHubRepo, Login, SponsorRecord, SponsorTotals, StripeEvent,
            TransactionRecord, TwitterProfile, User
        ]:
            for entity in model.all():
                db.delete(entity)
        flush_all()
        ctx.expire_cookie('auth')
        raise Redirect('/site.bootstrap')

# ------------------------------------------------------------------------------
# Init Local State
# ------------------------------------------------------------------------------

CAMPAIGN_CONTENT = render_markdown(read('page/gitfund.md'))

def init_state():

    for ident, duration, generator in [
        ('social.profiles', 300, get_social_profiles),
        ('sponsors', 60, get_sponsors),
    ]:
        CACHE_SPECS[ident] = CacheSpec(duration, generator)

    for spec in CAMPAIGN_TEAM:
        if spec.github:
            GITHUB_PROFILES.append(spec.github)
        if spec.twitter:
            TWITTER_PROFILES.append(spec.twitter)

    for profile in GITHUB_PROFILES:
        GITHUB_MEMCACHE_KEYS.append('github|%s' % profile)

    for profile in TWITTER_PROFILES:
        TWITTER_MEMCACHE_KEYS.append('twitter|%s' % profile)

    SOCIAL_MEMCACHE_KEYS.extend(GITHUB_MEMCACHE_KEYS)
    SOCIAL_MEMCACHE_KEYS.extend(TWITTER_MEMCACHE_KEYS)

    for plan, description in PLAN_DESCRIPTIONS.items():
        PLAN_DESCRIPTIONS[plan] = render_markdown(description.strip())

    for goal in CAMPAIGN_GOALS:
        goal.description = render_markdown(goal.description.strip())

    init_plan_info()

init_state()

# ------------------------------------------------------------------------------
# Suppress Warnings
# ------------------------------------------------------------------------------

_ = app
