# Public Domain (-) 2016-2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

from google.appengine.ext import db

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class BI(db.Model): # key=<incremented_id>, parent=<user>
    v = db.IntegerProperty(default=0)
    address = db.StringProperty(default='', indexed=False)
    company_name = db.StringProperty(default='', indexed=False)
    city = db.StringProperty(default='', indexed=False)
    created = db.DateTimeProperty(auto_now_add=True)
    country = db.StringProperty(default='', indexed=False)
    postcode = db.StringProperty(default='', indexed=False)
    sales_tax_id = db.StringProperty(default='', indexed=False)

BillingInfo = BI

class CP(db.Model): # key=<country_id>
    v = db.IntegerProperty(default=0)
    card_country = db.StringProperty(default='', indexed=False)
    card_id = db.StringProperty(default='', indexed=False)
    ip_address = db.StringProperty(default='', indexed=False)
    ip_city = db.StringProperty(default='', indexed=False)
    ip_country = db.StringProperty(default='', indexed=False)
    ip_latlng = db.StringProperty(default='', indexed=False)
    ip_region = db.StringProperty(default='', indexed=False)

CountryProof = CP

class CS(db.Model): # key=<cron_type_id>
    v = db.IntegerProperty(default=0)
    cursor = db.StringProperty(default='', indexed=False)

CronStatus = CS

class ER(db.Model): # key='latest'
    v = db.IntegerProperty(default=0)
    data = db.BlobProperty(default='')
    updated = db.DateTimeProperty(auto_now=True)

ExchangeRates = ER

class GP(db.Model): # key=<github_username>
    v = db.IntegerProperty(default=0)
    avatar = db.StringProperty(default='', indexed=False)
    description = db.TextProperty(default=u'')
    created = db.DateTimeProperty(auto_now_add=True)
    followers = db.IntegerProperty(default=0)
    joined = db.DateTimeProperty(indexed=False)
    name = db.StringProperty(default='', indexed=False)
    updated = db.DateTimeProperty(auto_now=True)

GitHubProfile = GP

class GR(db.Model): # key=<repo_id>
    v = db.IntegerProperty(default=0)
    stars = db.IntegerProperty(default=0)

GitHubRepo = GR

class L(db.Model): # key=<base32_encoded_email_lower>
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

StripeEvent = SE

class SR(db.Model): # key=<user_id>, parent=<ST:project_id>
    v = db.IntegerProperty(default=0)
    amount = db.IntegerProperty(default=0)
    currency = db.StringProperty(default='', indexed=False)
    plan = db.StringProperty(default='', indexed=False)

SponsorRecord = SR

class ST(db.Model): # key=<project_id>
    v = db.IntegerProperty(default=0)
    plans = db.TextProperty(default='')
    amounts = db.TextProperty(default='')

SponsorTotals = ST

class TP(db.Model): # key=<twitter_screen_name>
    v = db.IntegerProperty(default=0)
    avatar = db.StringProperty(default='', indexed=False)
    description = db.TextProperty(default=u'')
    created = db.DateTimeProperty(auto_now_add=True)
    followers = db.IntegerProperty(default=0)
    joined = db.DateTimeProperty(indexed=False)
    name = db.StringProperty(default='', indexed=False)
    updated = db.DateTimeProperty(auto_now=True)

TwitterProfile = TP

class TR(db.Model): # key=<stripe_event_id>, parent=<U|user_id>
    v = db.IntegerProperty(default=0)
    created = db.DateTimeProperty(auto_now_add=True)
    type = db.StringProperty(default='')   # 'invoice' | 'refund'

TransactionRecord = TR

class U(db.Model): # key=<auto>
    v = db.IntegerProperty(default=0)
    billing = db.IntegerProperty(default=0, indexed=False)
    created = db.DateTimeProperty(auto_now_add=True)
    delinquent = db.BooleanProperty(default=False)
    delinquent_email = db.BooleanProperty(default=False)
    email = db.StringProperty(default='', indexed=False)
    name = db.StringProperty(default='', indexed=False)
    plan = db.StringProperty(default='')
    status = db.StringProperty(default='')                           # 'created' | 'active' | 'cancelled'
    stripe_id = db.StringProperty(default='')                        # stripe customer id
    stripe_subscription = db.StringProperty(default='')              # stripe subscription id
    updated = db.DateTimeProperty(auto_now=True)

User = U
