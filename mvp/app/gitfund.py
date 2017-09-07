# -*- coding: utf-8 -*-

# Public Domain (-) 2015-2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

import logging
import re
import xml.etree.ElementTree as ET

from base64 import b32encode, b64encode
from cgi import escape
from collections import namedtuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
from json import dumps as encode_json, loads as decode_json
from random import choice
from struct import pack
from thread import allocate_lock
from threading import local
from time import time
from urllib import urlencode

from config import (
    ADMIN_AUTH_KEY, CAMPAIGN_DESCRIPTION, CAMPAIGN_TEAM, CAMPAIGN_TITLE,
    CANONICAL_HOST, GCS_BUCKET, GITHUB_ACCESS_TOKEN, GITHUB_CALLER_ID,
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, HMAC_KEY, LIVE, MAILJET_API_KEY,
    MAILJET_SECRET_KEY, MAILJET_SENDER_EMAIL, MAILJET_SENDER_NAME, ON_GOOGLE,
    OPEN_EXCHANGE_RATES_APP_ID, PAGES, PLAN_DESCRIPTIONS, SLACK_TOKEN,
    STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_TOKEN,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_CONSUMER_KEY,
    TWITTER_CONSUMER_SECRET
)

from model import (
    ExchangeRates, DonorTotals, GitHubProfile, GitHubRepo, Login,
    SponsorRecord, SponsorTotals, StripeEvent, TwitterProfile, User
)

from weblite import (
    app, Context, handle, NotFound, Redirect
)

import cloudstorage as gcs
import stripe

from emoji import EMOJI_MAP, EMOJI_SHORTCODES
from finance import (
    BASE_PRICES, CAMPAIGN_TARGET_FACTOR, PLAN_FACTORS, PLAN_SLOTS,
    TERRITORY2TAX
)

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
from prices import DETAILED_DEFAULT, PRICES_INDEX, PRICES_POS, TERRITORY2PRICES

from tavutil.crypto import (
    create_tamper_proof_string, secure_string_comparison,
    validate_tamper_proof_string
)

from territories import TERRITORIES, TERRITORY_CODES
from twitter import Client as TwitterClient

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

AUTH_HANDLERS = frozenset([
    'back.gitfund',
    'cancel.subscription',
    'manage.subscription',
    'update.sponsor.profile',
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

GRAVATAR_PREFIX = 'https://www.gravatar.com/avatar/'
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
    return val

def get_territory(ctx, default='US'):
    territory = ctx.environ.get('HTTP_X_APPENGINE_COUNTRY')
    if territory in TERRITORY_CODES:
        return territory
    return default

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

Context.CAMPAIGN_DESCRIPTION = CAMPAIGN_DESCRIPTION
Context.CAMPAIGN_TEAM = CAMPAIGN_TEAM
Context.CAMPAIGN_TITLE = CAMPAIGN_TITLE
Context.DETAILED_DEFAULT = DETAILED_DEFAULT
Context.LIVE = LIVE
Context.ON_GOOGLE = ON_GOOGLE
Context.PLAN_SLOTS = PLAN_SLOTS
Context.PLAN_DESCRIPTIONS = PLAN_DESCRIPTIONS
Context.PRICES_INDEX = PRICES_INDEX
Context.PRICES_POS = PRICES_POS
Context.STRIPE_PUBLISHABLE_KEY = STRIPE_PUBLISHABLE_KEY
Context.TERRITORIES = TERRITORIES
Context.TERRITORY2PRICES = TERRITORY2PRICES
Context.TERRITORY2TAX = TERRITORY2TAX

Context.current_year = staticmethod(current_year)
Context.get_site_sponsors = staticmethod(get_site_sponsors)
Context.get_sponsor_image_url = staticmethod(get_sponsor_image_url)
Context.get_territory = get_territory
Context.linkify_github_bio = staticmethod(linkify_github_bio)
Context.linkify_twitter_bio = staticmethod(linkify_twitter_bio)
Context.log = log
Context.noindex = False
Context.page_title = ''
Context.preview_mode = False
Context.pluralise = staticmethod(pluralise)
Context.show_sponsors_footer = False
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

Totals = namedtuple(
    'Totals', ['backers', 'donors', 'sponsor_plans', 'percent', 'progress']
)

def get_totals():
    cache = get_cache_multi(['sponsor.totals', 'donor.totals'])
    to_set = {}
    if 'sponsor.totals' in cache:
        sponsor_plans = cache['sponsor.totals']
    else:
        sponsor_plans = SponsorTotals.get_or_insert('gitfund').get_plans()
        to_set['sponsor.totals'] = sponsor_plans
    backers = raised = 0
    for plan, slots in sponsor_plans.iteritems():
        raised += slots * PLAN_FACTORS[plan]
        backers += slots
    if 'donor.totals' in cache:
        donors = cache['donor.totals']
    else:
        donors = DonorTotals.get_or_insert('gitfund').count
        to_set['donor.totals'] = donors
    if to_set:
        set_cache_multi(to_set, 20)
    backers += donors
    raised += donors * PLAN_FACTORS['donor']
    if not raised:
        percent = 0
        progress = ''
    else:
        pct = (raised / CAMPAIGN_TARGET_FACTOR) * 100
        if pct > 1:
            percent = int(pct)
        else:
            percent = 1
        progress = '%.2f%%' % pct
    return Totals(backers, donors, sponsor_plans, percent, progress)

SocialProfiles = namedtuple('SocialProfiles', ['github', 'repo', 'twitter'])

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
    return SocialProfiles(github, repo, twitter)

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
        'backing_started'
        ).run(batch_size=100):
        sponsors[sponsor.plan].append({
            'img': sponsor.get_image_spec(),
            'text': sponsor.get_link_text(),
            'url': sponsor.get_link_url(),
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
    if not ON_GOOGLE:
        logging.info("Skipping sending of email: %r" % subject)
        logging.info("Email body:\n%s\n" % body)
        return
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
# VAT Validation
# -----------------------------------------------------------------------------

INVALID_VAT_ID = "Invalid VAT ID."

def check_vat_id(vat_id):
    try:
        resp = validate_vat_id(vat_id, 1)
    except Exception as err:
        resp = "Unexpected error whilst validating. Please try again later."
        logging.error(
            "Unexpected error whilst validating VAT ID %r: %s" % (vat_id, err)
        )
    if isinstance(resp, basestring):
        if resp == INVALID_VAT_ID:
            return None, True, None
        return None, False, resp
    return encode_json(resp), False, None

def parse_vat_id(vat_id):
    vat_id = remove_invalid_vat_char('', vat_id.upper())
    if not vat_id:
        return
    id_len = len(vat_id)
    if (id_len < 4) or (id_len > 14):
        return
    country = vat_id[:2].upper()
    vat_number = vat_id[2:]
    if country not in TERRITORY2TAX:
        return
    handler = TERRITORY2TAX[country][1]
    if handler:
        vat_number = handler(vat_number)
    return country, vat_number

remove_invalid_vat_char = re.compile('[^A-Z0-9]+').sub

def validate_vat_id(vat_id, attempts, deadline=20):
    parsed = parse_vat_id(vat_id)
    if not parsed:
        return INVALID_VAT_ID
    payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:vies="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
  <soap:Body>
    <vies:checkVat>
      <vies:countryCode>%s</vies:countryCode>
      <vies:vatNumber>%s</vies:vatNumber>
    </vies:checkVat>
  </soap:Body>
</soap:Envelope>""" % parsed
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'urn:ec.europa.eu:taxud:vies:services:checkVat/checkVat'
    }
    last_attempt = attempts - 1
    for i in range(attempts):
        try:
            resp = urlfetch(
                'http://ec.europa.eu/taxation_customs/vies/services/checkVatService',
                payload, POST, headers=headers, deadline=deadline,
                validate_certificate=True,
            )
            if resp.status_code == 200:
                break
        except Exception:
            if i == last_attempt:
                return "Unable to reach the VAT validation service. Please try again later."
    def err(msg=''):
        if not msg:
            msg = "The VAT validation service is experiencing issues. Please try again later."
        logging.error("%s\n\n%r" % (msg, resp.content))
        return msg
    root = ET.fromstring(resp.content)
    body = root.find('{http://schemas.xmlsoap.org/soap/envelope/}Body')
    if body is None:
        return err()
    fault = body.find('{http://schemas.xmlsoap.org/soap/envelope/}Fault')
    if fault is not None:
        fault = fault.find('faultstring').text
        if fault == 'INVALID_INPUT':
            return INVALID_VAT_ID
        return err("Unable to validate VAT ID: %s. Please try again later." % fault)
    vatResp = body.find('{urn:ec.europa.eu:taxud:vies:services:checkVat:types}checkVatResponse')
    if vatResp is None:
        return err()
    valid = vatResp.find('{urn:ec.europa.eu:taxud:vies:services:checkVat:types}valid')
    if valid is None:
        return err()
    if valid.text == 'false':
        return INVALID_VAT_ID
    info = {}
    for child in vatResp:
        key = child.tag.split('}')[1]
        if key in ('valid', 'requestDate'):
            continue
        info[key] = child.text
    return info

# -----------------------------------------------------------------------------
# Backing Subscription
# -----------------------------------------------------------------------------

STRIPE_ERROR = "Sorry, there was an unexpected error with our payment processor. Please try again later."

def cancel_backing_txn(user_id, totals_need_syncing=True):
    user = User.get_by_id(user_id)
    if not user.backer:
        return user
    user.backer = False
    user.backing_started = None
    user.delinquent = False
    user.delinquent_emailed = False
    user.payment_type = ''
    user.plan = ''
    user.sponsor = False
    user.stripe_is_unpaid = False
    user.stripe_needs_updating = False
    if user.stripe_subscription:
        user.stripe_needs_cancelling.append(user.stripe_subscription)
        user.stripe_subscription = ''
    user.totals_need_syncing = totals_need_syncing
    user.totals_version += 1
    user.put()
    return user

def cancel_stripe_subscription(user_id, sub_id):
    try:
        sub = stripe.Subscription.retrieve(sub_id)
    except Exception as e:
        logging.error(
            "Error retrieving Stripe subscription %s for %s: %r"
            % (sub_id, user_id, e)
        )
        return "Sorry, there was an error accessing your subscription. Please try again later."
    if sub.status != 'canceled':
        try:
            sub.delete()
        except Exception as e:
            logging.error(
                "Error cancelling Stripe subscription %s for %s: %r"
                % (sub.id, user_id, e)
            )
            return "Sorry, there was an error cancelling your subscription. Please try again later."
    def txn():
        user = User.get_by_id(user_id)
        if sub_id in user.stripe_needs_cancelling:
            user.stripe_needs_cancelling.remove(sub_id)
            user.put()
    run_in_transaction(txn)

def check_subscription_status(ctx, user, user_id):
    sub_id = user.stripe_subscription
    try:
        sub = stripe.Subscription.retrieve(sub_id)
    except Exception as e:
        logging.error(
            "Error retrieving Stripe subscription %s for %s: %r"
            % (sub_id, user_id, e)
        )
        return "Sorry, there was an error accessing your subscription. Please try again later."
    status = sub.status
    def txn():
        user = User.get_by_id(user_id)
        if user.stripe_subscription != sub_id:
            return user
        if status == 'active':
            if user.delinquent:
                user.delinquent = False
                user.delinquent_emailed = False
            if user.stripe_is_unpaid:
                user.stripe_is_unpaid = False
        elif status == 'past_due':
            if not user.delinquent:
                user.delinquent = True
                user.delinquent_emailed = False
            if user.stripe_is_unpaid:
                user.stripe_is_unpaid = False
        elif status == 'canceled':
            user.backer = False
            user.backing_started = None
            user.delinquent = False
            user.delinquent_emailed = False
            user.payment_type = ''
            user.plan = ''
            user.sponsor = False
            user.stripe_is_unpaid = False
            user.stripe_needs_updating = False
            user.stripe_subscription = ''
            user.totals_need_syncing = True
            user.totals_version += 1
        elif status == 'unpaid':
            user.stripe_is_unpaid = True
        user.put()
        return user
    user = run_in_transaction(txn)
    if user.delinquent and not user.delinquent_emailed:
        authlink = ctx.compute_url('login', 'back.gitfund', email=user.email, existing='1')
        err = ctx.send_email(
            "Payment failure. Please update your card details",
            user.name, user.email, 'delinquent', authlink=authlink
            )
        if err:
            return err
        def mark_as_emailed():
            user = User.get_by_id(user_id)
            if user.delinquent:
                user.delinquent_emailed = True
                user.put()
        run_in_transaction(mark_as_emailed)

def get_stripe_plan(plan, territory):
    idx = PRICES_POS[plan + '-plan-id']
    return PRICES_INDEX[TERRITORY2PRICES[territory]][idx]

def handle_cancellation(user_id, totals_need_syncing=True):
    user = run_in_transaction(cancel_backing_txn, user_id, totals_need_syncing)
    err = handle_stripe_cancellation(user, user_id)
    return user, err

def handle_stripe_cancellation(user, user_id):
    err = None
    for sub_id in user.stripe_needs_cancelling:
        stripe_err = cancel_stripe_subscription(user_id, sub_id)
        if stripe_err and not err:
            err = stripe_err
    return err

def sync_backer(ctx, user, first_time=False):
    err = []
    user_id = user.key().id()
    # Sync the totals.
    while user.totals_need_syncing:
        totals_version = user.totals_version
        maxed = run_in_transaction(
            sync_totals_txn, str(user_id), user.plan, totals_version
        )
        if maxed == 'old.version':
            user = User.get_by_id(user_id)
            continue
        if maxed:
            plan = user.plan
            user, _err = handle_cancellation(user_id, totals_need_syncing=False)
            err.append(
                "Sorry, there are no %s sponsorship slots left."
                % plan.title()
            )
            if _err:
                err.append(_err)
        else:
            def txn():
                user = User.get_by_id(user_id)
                if user.totals_need_syncing and totals_version == user.totals_version:
                    user.totals_need_syncing = False
                    user.put()
                return user
            user = run_in_transaction(txn)
        break
    # Create/update the Stripe subscription.
    if user.stripe_needs_updating:
        try:
            if user.stripe_subscription:
                create_sub = False
            else:
                create_sub = True
            if create_sub:
                subscription = stripe.Subscription.create(
                    customer=user.stripe_customer_id,
                    idempotency_key=user.get_stripe_idempotency_key(),
                    metadata=user.get_stripe_meta(),
                    plan=get_stripe_plan(user.plan, user.territory),
                )
        except stripe.error.CardError as e:
            err.append(
                "Sorry, there was an error processing your payment: %s"
                % e.json_body['error']['message']
            )
        except Exception as e:
            logging.error(
                "Error handling subscription for %r on %r plan: %r"
                % (user.stripe_customer_id, user.plan, e)
            )
            err.append(
                "Sorry, there was an unexpected error with our payment processor. Please try again later."
            )
        if not err:
            stripe_version = user.stripe_update_version
            sub_id = subscription.id
            def txn():
                user = User.get_by_id(user_id)
                if user.stripe_needs_updating and stripe_version == user.stripe_update_version:
                    user.stripe_subscription = sub_id
                    user.stripe_needs_updating = False
                    user.put()
                elif sub_id not in user.stripe_needs_cancelling:
                    user.stripe_needs_cancelling.append(sub_id)
                    user.put()
                return user
            user = run_in_transaction(txn)
    # Cancel any outstanding subscriptions.
    if user.stripe_needs_cancelling:
        _err = handle_stripe_cancellation(user, user_id)
        if _err:
            err.append(_err)
    # Skip the VAT ID and delinquency checks if it is the first time.
    if first_time:
        if err:
            logging.error(
                "There were issues syncing backer info for %s: %r"
                % (user_id, err)
            )
        return err
    # Check the VAT ID if necessary.
    if user.tax_id_to_validate:
        tax_info, is_invalid, _err = check_vat_id(user.tax_id)
        if not _err:
            def txn(tax_id):
                user = User.get_by_id(user_id)
                if not user.tax_id_to_validate:
                    return user
                if user.tax_id != tax_id:
                    return user
                if is_invalid:
                    user.tax_id_detailed = ''
                    user.tax_id_is_invalid = True
                else:
                    user.tax_id_detailed = tax_info
                    user.tax_id_is_invalid = False
                user.tax_id_to_validate = False
                user.put()
                return user
            user = run_in_transaction(txn, user.tax_id)
        if _err:
            err.append(_err)
    # Check if the subscription is past_due or has been cancelled.
    if user.stripe_subscription:
        _err = check_subscription_status(ctx, user, user_id)
        if _err:
            err.append(_err)
    if err:
        logging.error(
            "There were issues syncing backer info for %s: %r"
            % (user_id, err)
        )
    return err

# TODO(tav): It's possible for this to return different results depending on the
# order of retry.
def sync_totals_txn(user_id, plan, version):
    totals = SponsorTotals.get_by_key_name('gitfund')
    plans = totals.get_plans()
    record = SponsorRecord.get_by_key_name(user_id, parent=totals)
    if not record:
        record = SponsorRecord(key_name=user_id, parent=totals)
    if record.version > version:
        return 'old.version'
    if record.plan:
        plans[record.plan] -= 1
        record.plan = ''
    maxed = False
    if plan in PLAN_SLOTS:
        if plans[plan] >= PLAN_SLOTS[plan]:
            maxed = True
        else:
            record.plan = plan
            plans[plan] += 1
    record.version = version
    totals.set_plans(plans)
    db.put([totals, record])
    return maxed

# -----------------------------------------------------------------------------
# Other Utility Functions
# -----------------------------------------------------------------------------

create_key = db.Key.from_path

def create_user(name, email):
    login_key = get_login_key_name(email)
    login = Login.get_or_insert(login_key)
    if login.user_id:
        return User.get_by_id(login.user_id)
    user = User(email=email, name=name)
    user.put()
    new_user_id = user.key().id()
    def txn(user_id):
        login = Login.get_by_key_name(login_key)
        if login.user_id:
            return login.user_id
        login.user_id = user_id
        login.put()
        return user_id
    user_id = run_in_transaction(txn, new_user_id)
    if user_id == new_user_id:
        return user
    return User.get_by_id(user_id)

def is_email(email, match_addr=re.compile(r'.+\@.+').match):
    if not match_addr(email):
        return
    if len(email.encode('utf-8')) > 254:
        return
    return True

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
# Campaign Content Rendering
# -----------------------------------------------------------------------------

TOTAL_SLOTS = sum(PLAN_SLOTS.values())
URGE_SPONSOR = """, or even better, by getting your company
<a href="/back.gitfund?plan=bronze">to sponsor GitFund</a> &mdash; """

def process_campaign_content():
    segments = []; append = segments.append
    for segment in render_markdown(read('page/gitfund.md')).split('VAR'):
        if not segment.startswith('-'):
            append(segment)
            continue
        varname, content = segment.split('-SLOT')
        varname = varname[1:].lower()
        if varname == 'available':
            append((varname, -1))
        else:
            append((varname, PRICES_POS[varname]))
        append(content)
    return segments

def render_campaign_content(ctx, territory, taken):
    segments = []; append = segments.append
    prices = PRICES_INDEX[TERRITORY2PRICES[territory]]
    for segment in CONTENT_SEGMENTS:
        if isinstance(segment, basestring):
            append(segment)
        else:
            ident, idx = segment
            if ident == 'available':
                avail = max(TOTAL_SLOTS - sum(taken.values()), 0)
                avail = TOTAL_SLOTS
                if avail:
                    append(URGE_SPONSOR)
                    if avail == TOTAL_SLOTS:
                        append('there are only %d sponsorship slots available.' % avail)
                    elif avail == 1:
                        append('there is only %d sponsorship slot left.' % avail)
                    else:
                        append('there are only %d sponsorship slots left.' % avail)
                else:
                    append('.')
            else:
                append('<span class="price-info-%s">' % ident)
                append(prices[idx])
                append('</span>')
    return u''.join(segments)

CONTENT_SEGMENTS = process_campaign_content()

Context.render_campaign_content = render_campaign_content

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
        raise Redirect('/users.list')
    if key is None:
        return {}
    ctx.validate_xsrf(xsrf)
    if not secure_string_comparison(key, ADMIN_AUTH_KEY):
        logging.warn("Invalid auth attempt.")
        return {
            "error": "Invalid auth key. This failed attempt has been logged for security purposes."
        }
    ctx.set_secure_cookie('admin', ADMIN_AUTH_KEY)
    raise Redirect('/users.list')

@handle
def auth(ctx, token=None, return_to=None):
    if not token:
        raise NotFound
    if return_to not in AUTH_HANDLERS:
        raise NotFound
    user_id = validate_tamper_proof_string('authtoken', token, HMAC_KEY, True)
    if not user_id:
        return "<h1>Sorry, this auth link has expired.</h1>"
    ctx.set_secure_cookie('auth', user_id)
    raise Redirect('/' + return_to)

@handle(['back.gitfund', 'site'])
def back_gitfund(
    ctx, name='', email='', plan='', territory='', tax_id='', card='',
    xsrf=None
    ):
    ctx.page_title = "Back GitFund!"
    ctx.stripe_js = True
    if not LIVE:
        ctx.preview_mode = True
    kwargs = {
        'card': card,
        'email': email,
        'name': name,
        'plan': plan,
        'tax_id': tax_id,
        'territory': territory,
    }
    user = ctx.user
    if user:
        kwargs['email'] = user.email
        kwargs['exists'] = True
        kwargs['exists_plan'] = user.plan
    if not xsrf:
        if user:
            kwargs['name'] = user.name
            if plan:
                kwargs['plan'] = plan
            else:
                kwargs['plan'] = user.plan
            kwargs['tax_id'] = user.tax_id
            kwargs['tax_id_is_invalid'] = user.tax_id_is_invalid
            kwargs['territory'] = user.territory
        return kwargs
    ctx.log(kwargs)
    # Validate input.
    ctx.validate_xsrf(xsrf)
    def error(msg, html=False):
        if html:
            kwargs['error_html'] = msg
        else:
            kwargs['error'] = msg
        return kwargs
    if not user:
        name = name.strip()
        if not name:
            return error("Please specify your name.")
        if len(name.encode('utf-8')) > 60:
            return error("Your name must be less than 60 bytes long.")
        email = email.strip()
        if not email:
            return error("Please provide your email address.")
        if not is_email(email):
            return error("Please provide a valid email address.")
    if plan not in PLAN_FACTORS:
        return error("Please select a support tier.")
    if territory not in TERRITORY_CODES:
        return error("Please select your country.")
    if territory in TERRITORY2TAX:
        if plan == 'donor':
            tax_id = ''
        else:
            tax_id = tax_id.strip()
            if (not tax_id) or (len(tax_id) < 4):
                return error("Please provide your VAT ID.")
            tax_prefix = TERRITORY2TAX[territory][0]
            if tax_id[:2].upper() != tax_prefix:
                return error("Please provide a VAT ID for the selected country.")
            if user and user.tax_id == tax_id:
                if user.tax_id_to_validate:
                    validate = True
                elif user.tax_id_is_invalid:
                    return error(INVALID_VAT_ID)
                else:
                    tax_info = user.tax_id_detailed
                    validate = False
            else:
                validate = True
            if validate:
                tax_info, is_invalid, _ = check_vat_id(tax_id) # COST(1)
                if is_invalid:
                    return error(INVALID_VAT_ID)
    else:
        tax_id = ''
    kwargs['card'] = ''
    card = card.strip()
    # Check if we already have a Sponsor record for the given email address.
    def existing_backer():
        link = ctx.compute_url("login", "back.gitfund", email=email, existing='1')
        return error(
            'There is already an active backing set up for %s. Please <a href="%s">sign in</a> to update your details.'
            % (escape(email), link), html=True
        )
    if user:
        user_id = ctx.user_id
    else:
        user = get_user_from_email(email) # COST(2)
        if user and user.backer:
            return existing_backer()
        # Create a new user if there's no existing user record.
        if user is None:
            user = create_user(name, email) # COST(2-4)
        user_id = user.key().id()
        ctx._user_id = user_id
        ctx._user = user
        ctx.set_secure_cookie('auth', str(user_id))
        kwargs['exists'] = True
    # Create a Stripe Customer record if it doesn't exist.
    if user.stripe_customer_id:
        cus_exists = True
    else:
        try:
            customer = stripe.Customer.create(email=email) # COST(1)
        except Exception as e:
            logging.error("Error creating Stripe customer with email %s: %r" % (email, e))
            return error(STRIPE_ERROR)
        def txn():
            user = User.get_by_id(user_id)
            if user.stripe_customer_id:
                return user, True
            user.stripe_customer_id = customer.id
            user.put()
            return user, False
        user, cus_exists = run_in_transaction(txn) # COST(1)
        ctx._user = user
    # Ensure card token exists where customer hasn't already been created.
    if (not cus_exists) and (not card):
        return error("Please enable JavaScript before filling in your card details.")
    if card:
        # Retrieve the existing customer if it already exists.
        if cus_exists:
            try:
                customer = stripe.Customer.retrieve(user.stripe_customer_id)
            except Exception as e:
                logging.error("Error retrieving Stripe customer %s: %r" % (user.stripe_customer_id, e))
                return error(STRIPE_ERROR)
        # Add the new card as the default source.
        try:
            customer.default_source = customer.sources.create(source=card).id # COST(1)
            customer.save() # COST(1)
        except stripe.error.CardError as e:
            logging.error("Error adding card to Stripe customer %s: %r" % (user.stripe_customer_id, e))
            return error("Sorry, there was an error processing your payment: %s" % e.json_body['error']['message'])
        except Exception as e:
            logging.error("Error adding card to Stripe customer %s: %r" % (user.stripe_customer_id, e))
            return error(STRIPE_ERROR)
    # Check that a sponsorship slot is available.
    if plan != user.plan and plan in PLAN_SLOTS:
        slots = PLAN_SLOTS[plan]
        totals = SponsorTotals.get_by_key_name('gitfund') # COST(1)
        plans = totals.get_plans()
        if plans[plan] >= slots:
            return error("Sorry, there are no %s sponsorship slots left." % plan.title())
    # Set up or update sponsorship.
    def txn():
        user = User.get_by_id(user_id)
        user.payment_type = 'stripe'
        first_time = False
        if not user.backer:
            first_time = True
            user.backer = True
            user.backing_started = datetime.utcnow()
        new_stripe_plan = get_stripe_plan(plan, territory)
        if user.plan:
            existing_stripe_plan = get_stripe_plan(user.plan, user.territory)
            if plan != user.plan:
                user.totals_need_syncing = True
                user.totals_version += 1
        else:
            existing_stripe_plan = ''
            if plan != 'donor':
                user.totals_need_syncing = True
                user.totals_version += 1
        user.plan = plan
        if plan in PLAN_SLOTS:
            user.sponsor = True
        else:
            user.sponsor = False
        if existing_stripe_plan != new_stripe_plan:
            if user.stripe_subscription:
                user.stripe_needs_cancelling.append(user.stripe_subscription)
            user.stripe_needs_updating = True
            user.stripe_subscription = ''
            user.stripe_update_version += 1
        elif card and not user.stripe_subscription:
            user.stripe_update_version += 1
        if tax_id:
            user.tax_id = tax_id
            if tax_info:
                user.tax_id_detailed = tax_info
                user.tax_id_to_validate = False
                user.tax_id_is_invalid = False
            else:
                user.tax_id_detailed = ''
                user.tax_id_to_validate = True
                user.tax_id_is_invalid = False
        else:
            user.tax_id = ''
            user.tax_id_detailed = ''
            user.tax_id_to_validate = False
            user.tax_id_is_invalid = False
        user.territory = territory
        user.put()
        return user, first_time
    user, first_time = run_in_transaction(txn) # COST(1)
    ctx._user = user
    err = sync_backer(ctx, user, first_time)
    if err:
        return error(err[0])
    delete_cache_multi(['sponsors', 'sponsor.totals', 'donor.totals'])
    if user.sponsor and (not user.link_text) and (not user.link_url):
        raise Redirect('/update.sponsor.profile?setup=1')
    if first_time:
        raise Redirect('/tav/gitfund?thanks=1')
    return {'updated': True}

@handle(['cancel.subscription', 'site'], anon=False)
def cancel_subscription(ctx, xsrf=None):
    ctx.page_title = "Cancel Subscription"
    user = ctx.user
    if not user.backer:
        return {
            'error': "Sorry, no active subscription found for %s." % user.email
        }
    if xsrf is None:
        return {
            'backer': user
        }
    ctx.validate_xsrf(xsrf)
    user, err = handle_cancellation(ctx.user_id)
    if err:
        return {'error': err}
    err = sync_backer(ctx, user)
    if err:
        return {'error': err}
    delete_cache_multi(['sponsors', 'sponsor.totals', 'donor.totals'])
    return {'cancelled': True}

@handle(['community', 'site'])
def community(ctx, email=None, xsrf=''):
    ctx.page_title = "Slack/IRC Community"
    ctx.show_sponsors_footer = True
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

@handle(admin=True)
def compare_currencies(ctx):
    rates = decode_json(
        ExchangeRates.get_by_key_name('latest').data, parse_float=Decimal
        )['rates']
    data = []
    usd_value = BASE_PRICES['USD'][-1]
    dec_places_2 = Decimal('0.01')
    dec_places_4 = Decimal('0.0001')
    for currency in BASE_PRICES:
        value = Decimal(BASE_PRICES[currency][-1])
        current = rates[currency] * usd_value
        cur_dec = Decimal(current).quantize(dec_places_2, ROUND_HALF_UP)
        ratio = (value / current).quantize(dec_places_4, ROUND_HALF_UP)
        data.append((currency, ratio, cur_dec, value))
    data = sorted(data, key=lambda row: (row[1], row[0]))
    ctx.response_headers['Content-Type'] = 'text/plain'
    hdr = 'Symbol\t\tRatio\t\tCurrent\t\tPreset\n\n'
    return hdr + '\n'.join("%s\t\t%s%17s%15s" % row for row in data)

@handle
def cron_donors(ctx):
    count = 0
    for backer in User.all().filter('backer =', True).filter(
        'sponsor =', False
    ).run(batch_size=1000, keys_only=True):
        count += 1
    totals = DonorTotals.get_or_insert('gitfund')
    totals.count = count
    totals.put()
    delete_cache('donor.totals')
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
def cron_sync(ctx):
    for user in User.all().filter(
        'updated <=', datetime.utcnow() - timedelta(minutes=10)
    ).order('updated'):
        sync_backer(ctx, user)

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

@handle(['login', 'site'])
def login(ctx, return_to='', email='', existing=False, xsrf=None):
    ctx.page_title = "Log in to GitFund"
    if return_to:
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
    if return_to:
        intent = return_to.split('.')
        intent_button = ' '.join(part.title() for part in intent)
    else:
        intent = ['log in into', 'account']
        intent_button = 'Login Link'
        return_to = 'manage.subscription'
    authlink = ctx.compute_url('auth', token, return_to)
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

@handle(['manage.subscription', 'site'], anon=False)
def manage_subscription(ctx):
    ctx.page_title = "Manage Subscription"

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
    url = get_sponsor_image_url(sponsor, size)
    resp = urlfetch(url, validate_certificate=True)
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
    ctx.show_sponsors_footer = True
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

@handle(['site.donors', 'site'])
def site_donors(ctx, cursor=None):
    ctx.page_title = "Our Donors"
    q = User.all().filter('backer =', True).filter(
        'sponsor =', False).order('backing_started')
    if cursor:
        q = q.with_cursor(cursor)
        cursor = None
    donors = []
    prev_point = None
    idx = 0
    for donor in q.run(batch_size=100):
        idx += 1
        if idx == 100:
            cursor = prev_point
            break
        elif idx == 99:
            prev_point = q.cursor()
        donors.append(donor)
    return {
        'cursor': cursor,
        'donors': donors,
    }

@handle(['site.sponsors', 'site'])
def site_sponsors(ctx, cursor=None):
    ctx.page_title = "Our Sponsors"
    return {
        'sponsors': get_local('sponsors')
    }

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
def tav(ctx, project='', thanks=None, **kwargs):
    if project != 'gitfund':
        raise NotFound
    ctx.preview_mode = True
    ctx.show_sponsors_footer = True
    ctx.site_description = CAMPAIGN_DESCRIPTION
    ctx.site_image = ctx.site_url + ctx.STATIC("gfx/cover.lossy.jpeg")
    ctx.site_image_attribution = SIMG
    ctx.site_title = CAMPAIGN_TITLE
    return {
        'social': get_local('social.profiles'),
        'territory': ctx.get_territory(),
        'totals': get_local('totals'),
        'thanks': thanks,
    }

@handle(['update.sponsor.profile', 'site'], anon=False)
def update_sponsor_profile(
    ctx, link_text='', link_url='', image=None, setup='', xsrf=None
    ):
    ctx.page_title = "Update Sponsor Profile"
    if xsrf is None:
        return {
            'link_text': ctx.user.get_link_text(),
            'link_url': ctx.user.link_url,
            'setup': setup,
        }
    def error(msg):
        return {
            'error': msg,
            'link_text': link_text,
            'link_url': link_url,
        }
    link_text = link_text.strip()
    if link_text and len(link_text.encode('utf-8')) > 60:
        return error("The link text must be less than 60 bytes long.")
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
        if (float(width) / height) > 3:
            return error("Sorry, the width of the image cannot be more than 3 times its height.")
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
    run_in_transaction(txn)
    delete_cache('sponsors')
    raise Redirect('/tav/gitfund?thanks=1')

@handle(['users.list', 'site'])
def users_list(ctx, cursor=None):
    site.page_title = "Users List"
    if not ctx.is_admin:
        raise Redirect('/admin')
    q = User.all().order('-updated')
    if cursor:
        q = q.with_cursor(cursor)
        cursor = None
    users = []
    prev_point = None
    for user in q.run(batch_size=100):
        if len(users) == 100:
            cursor = prev_point
            break
        users.append(user)
        prev_point = q.cursor()
    return {
        'cursor': cursor,
        'users': users,
    }

@handle(admin=True)
def validate_vat(ctx, vat_id):
    ctx.log({"vat_id": vat_id})
    ctx.response_headers["Content-Type"] = "text/plain"
    resp, is_invalid, err = check_vat_id(vat_id)
    if is_invalid:
        return INVALID_VAT_ID
    if err:
        return "ERROR: " + resp
    return resp

# ------------------------------------------------------------------------------
# Dev Handlers
# ------------------------------------------------------------------------------

if not LIVE:

    def xsrf_url(ctx, **kwargs):
        url = escape(ctx.compute_url(ctx.name, xsrf=ctx.xsrf_token, **kwargs))
        return '<a href="%s">%s</a>' % (url, url)

    @handle(admin=True)
    def site_bootstrap(ctx, xsrf=None):
        if not xsrf:
            return xsrf_url(ctx)
        ctx.validate_xsrf(xsrf)
        cron_github(ctx)
        cron_twitter(ctx)
        return 'OK'

    @handle(admin=True)
    def site_flush(ctx, xsrf=None):
        if not xsrf:
            return xsrf_url(ctx)
        ctx.validate_xsrf(xsrf)
        flush_all()
        return 'OK'

    @handle(admin=True)
    def site_wipe(ctx, xsrf=None):
        if not xsrf:
            return xsrf_url(ctx)
        ctx.validate_xsrf(xsrf)
        for model in [
            ExchangeRates, DonorTotals, GitHubProfile, GitHubRepo, Login,
            SponsorRecord, SponsorTotals, StripeEvent, TwitterProfile, User
        ]:
            for entity in model.all():
                db.delete(entity)
        flush_all()
        ctx.expire_cookie('auth')
        raise Redirect('/site.bootstrap')

# ------------------------------------------------------------------------------
# Init Local State
# ------------------------------------------------------------------------------

def init_state():

    for ident, duration, generator in [
        ('social.profiles', 300, get_social_profiles),
        ('sponsors', 20, get_sponsors),
        ('totals', 20, get_totals),
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

init_state()

# ------------------------------------------------------------------------------
# Suppress Warnings
# ------------------------------------------------------------------------------

_ = app
