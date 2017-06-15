# Public Domain (-) 2016-2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

from google.appengine.ext import db
from hashlib import md5
from json import dumps as encode_json, loads as decode_json
from minfin import PLAN_VERSION

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class GP(db.Model): # key=<github_username>
    v = db.IntegerProperty(default=0)
    avatar = db.StringProperty(default='', indexed=False)
    description = db.TextProperty(default=u'')
    created = db.DateTimeProperty(auto_now_add=True)
    followers = db.IntegerProperty(default=0, indexed=False)
    joined = db.DateTimeProperty(indexed=False)
    name = db.StringProperty(default='', indexed=False)
    updated = db.DateTimeProperty(auto_now=True)

GitHubProfile = GP

class GR(db.Model): # key=<repo_id>
    v = db.IntegerProperty(default=0)
    stars = db.IntegerProperty(default=0, indexed=False)

GitHubRepo = GR

class L(db.Model): # key=e.<base32_encoded_email_lower>
    v = db.IntegerProperty(default=0)
    user_id = db.IntegerProperty(default=0)

Login = L

class SE(db.Model): # key=<stripe_event_id>
    v = db.IntegerProperty(default=0)
    created = db.IntegerProperty(default=0)
    customer = db.StringProperty(default='')
    data = db.BlobProperty(default='')
    event_type = db.StringProperty(default='')
    livemode = db.BooleanProperty(default=False)
    state = db.IntegerProperty(default=0)

StripeEvent = SE

class SR(db.Model): # key=<user_id>, parent=<ST:project_id>
    v = db.IntegerProperty(default=0)
    plan = db.StringProperty(default='', indexed=False)
    version = db.IntegerProperty(default=0, indexed=False)

SponsorRecord = SR

class ST(db.Model): # key=<project_id>
    v = db.IntegerProperty(default=0)
    plans = db.TextProperty(default='')

    def get_plans(self):
        if not self.plans:
            return {'bronze': 0, 'silver': 0, 'gold': 0, 'platinum': 0}
        return decode_json(self.plans)

    def set_plans(self, plans):
        self.plans = encode_json(plans)

SponsorTotals = ST

class TP(db.Model): # key=<twitter_screen_name>
    v = db.IntegerProperty(default=0)
    avatar = db.StringProperty(default='', indexed=False)
    description = db.TextProperty(default=u'')
    created = db.DateTimeProperty(auto_now_add=True)
    followers = db.IntegerProperty(default=0, indexed=False)
    joined = db.DateTimeProperty(indexed=False)
    name = db.StringProperty(default='', indexed=False)
    updated = db.DateTimeProperty(auto_now=True)

TwitterProfile = TP

class U(db.Model): # key=<auto>
    v = db.IntegerProperty(default=0)
    created = db.DateTimeProperty(auto_now_add=True)
    delinquent = db.BooleanProperty(default=False)
    delinquent_email = db.BooleanProperty(default=False)
    email = db.StringProperty(default='', indexed=False)
    image_id = db.ByteStringProperty(default='', indexed=False)
    link_text = db.StringProperty(default='', indexed=False)
    link_url = db.StringProperty(default='', indexed=False)
    name = db.StringProperty(default='', indexed=False)
    needs_syncing = db.BooleanProperty(default=False)
    plan = db.StringProperty(default='')
    sponsor = db.BooleanProperty(default=False)
    sponsor_type = db.StringProperty(default='')                     # 'stripe' | 'manual'
    sponsorship_started = db.DateTimeProperty()
    stripe_customer_id = db.StringProperty(default='', indexed=False)
    stripe_needs_cancelling = db.ListProperty(str, indexed=False)
    stripe_needs_updating = db.BooleanProperty(default=False)
    stripe_subscription = db.StringProperty(default='')              # stripe subscription id
    stripe_update_version = db.IntegerProperty(default=0, indexed=False)
    tax_id = db.StringProperty(default='', indexed=False)
    tax_id_detailed = db.TextProperty(default=u'')
    tax_id_is_invalid = db.BooleanProperty(default=False)
    tax_id_to_validate = db.BooleanProperty(default=False)
    territory = db.StringProperty(default='')
    totals_need_syncing = db.BooleanProperty(default=False)
    totals_version = db.IntegerProperty(default=0, indexed=False)
    updated = db.DateTimeProperty(auto_now=True)

    # A tuple with the first indicating the type of image available:
    #
    # 'b' - blob stored in gcs
    # 'g' - md5 hash of the email for use with gravatar
    # 'u' - direct url of image
    def get_image_spec(self):
        if self.image_id:
            return ('b', self.image_id)
        return ('g', md5(self.email.lower()).hexdigest())

    def get_link_text(self):
        if self.link_text:
            return self.link_text
        return self.name

    def get_link_url(self):
        return self.link_url

    def get_stripe_idempotency_key(self):
        return '%s.%s' % (self.key().id(), self.stripe_update_version)

    def get_stripe_meta(self):
        return {"version": str(self.stripe_update_version)}

    def get_stripe_plan(self):
        if self.territory in ('GB', 'IM'):
            return "%s.v%d.gb" % (self.plan, PLAN_VERSION)
        return "%s.v%d" % (self.plan, PLAN_VERSION)

    def set_needs_syncing(self):
        if (self.stripe_needs_cancelling or self.stripe_needs_updating or
            self.tax_id_to_validate or self.totals_need_syncing):
            self.needs_syncing = True
        else:
            self.needs_syncing = False

User = U
