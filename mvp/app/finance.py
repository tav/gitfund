# Public Domain (-) 2016-2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

from decimal import Decimal

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

CAMPAIGN_TARGET_FACTOR = Decimal(3500)

CONTENT_FACTORS = {
    'example-gold': 250,
    'example-silver': 50,
    'example-bronze': 5,
    'target': int(CAMPAIGN_TARGET_FACTOR)
}

PLAN_FACTORS = {
    'donor': 1,
    'bronze': 50,
    'silver': 100,
    'gold': 250,
    'platinum': 500
}

PLAN_SLOTS = {
    'bronze': 50,
    'silver': 25,
    'gold': 10,
    'platinum': 5
}

PLAN_VERSION = 1

# From:
# https://support.stripe.com/questions/which-zero-decimal-currencies-does-stripe-support
ZERO_DECIMAL_CURRENCIES = frozenset([
    'BIF', 'CLP', 'DJF', 'GNF', 'JPY', 'KMF', 'KRW', 'MGA', 'PYG', 'RWF',
    'VND', 'VUV', 'XAF', 'XOF', 'XPF'
])

# -----------------------------------------------------------------------------
# Plan Prices
# -----------------------------------------------------------------------------

# Only defining native prices for countries in the EU (as it simplifies charging
# VAT), and for the top 60 territories based on Stack Overflow traffic:
# https://www.quantcast.com/stackoverflow.com#/geographicCard
#
# Ignoring currencies which are not supported on Stripe, e.g.
#
#     Bahraini Dinar (BHD), pegged at 1 USD == 0.376 BHD
#     Belarusian Ruble (BYR)
#     Bhutanese Ngultrum (BTN), pegged 1:1 to INR
#     Iranian Rial (IRR)
#     Kuwaiti Dinar (KWD), pegged to USD
#     Manx Pound (IMP), pegged 1:1 to GBP
#     Venezuelan Boliva (VEF)
#
# To determine price, look at exchange rate against USD price for the last year,
# including 2% Stripe fee for everything except GBP and EUR, take the high, and
# then round to nearest digit for 2-digits, nearest ten for 3-digits, etc.
#
BASE_PRICES = {
    'AED': [45],    # Pegged @ 1 USD == 3.6725 AED
    'ARS': [220],
    'AUD': [18],
    'BDT': [1100],
    'BGN': [24],
    'BRL': [44],
    'CAD': [17],
    'CHF': [13],
    'CLP': [8400],
    'COP': [39000],
    'CNY': [86],
    'CZK': [320],
    'DKK': [88],
    'EGP': [240],
    'EUR': [12],
    'GBP': [10],
    'HKD': [96],    # Pegged to USD
    'HRK': [89],
    'HUF': [3700],
    'IDR': [170000],
    'ILS': [48],
    'INR': [850],
    'JPY': [1500],
    'KRW': [15000],
    'LKR': [1900],
    'MAD': [125],
    'MXN': [270],
    'MYR': [56],
    'NGN': [4500],
    'NOK': [110],
    'NZD': [18],
    'PEN': [43],
    'PHP': [630],
    'PKR': [1400],
    'PLN': [53],
    'RON': [54],
    'RSD': [1500],
    'RUB': [820],
    'SAR': [47],    # Pegged @ 1 USD == 3.75 SAR
    'SEK': [120],
    'SGD': [18],
    'THB': [450],
    'TRY': [48],
    'TWD': [400],
    'UAH': [340],
    'USD': [12],
    'VND': [280000],
    'ZAR': [180],
}

# TODO(tav): Figure out what to do about currencies which are pegged to one of
# our accepted ones, e.g. the Brunei Dollar is 1:1 to the Singapore Dollar, and
# they are both managed by the Monetary Authority of Singapore.
#
# For now, override just the ones which are pegged 1:1 with one of our accepted
# ones through a currency board. Ignoring those with a non 1:1 exchange rate,
# e.g.
#
#     'ACD': 'USD',
#     'BAM': 'EUR',
#     'DJF': 'USD',
#     'KYD': 'USD',
#     'MOP': 'HKD',
#
PEGGED = {
    'BND': 'SGD',
    'BSD': 'USD',
    'FKP': 'GBP',
    'GIP': 'GBP',
    'LSL': 'ZAR',
    'NAD': 'ZAR',
    'SHP': 'GBP',
    'SZL': 'ZAR',
}

for _pegged, _base_currency in PEGGED.items():
    BASE_PRICES[_pegged] = BASE_PRICES[_base_currency]

del _pegged
del _base_currency

# -----------------------------------------------------------------------------
# Tax ID Handlers
# -----------------------------------------------------------------------------

def handle_austrian_vat_id(id):
    if not id.upper().startswith('U'):
        return 'U' + id
    return id

def handle_belgian_vat_id(id):
    if len(id) == 9:
        return '0' + id
    return id

# -----------------------------------------------------------------------------
# Tax Spec
# -----------------------------------------------------------------------------

TERRITORY2TAX = {
  'AT': ['AT', handle_austrian_vat_id],
  'AT-JU': ['AT', handle_austrian_vat_id],
  'AT-MI': ['AT', handle_austrian_vat_id],
  'BE': ['BE', handle_belgian_vat_id],
  'BG': ['BG', None],
  'CY': ['CY', None],
  'CZ': ['CZ', None],
  'DE': ['DE', None],
  'DK': ['DK', None],
  'EE': ['EE', None],
  'EL': ['EL', None],
  'ES': ['ES', None],
  'FI': ['FI', None],
  'FR': ['FR', None],
  'GB': ['GB', None],
  'GR': ['GR', None],
  'GR-81': ['GR', None],
  'GR-82': ['GR', None],
  'GR-83': ['GR', None],
  'GR-84': ['GR', None],
  'GR-85': ['GR', None],
  'GR-NS': ['GR', None],
  'GR-ST': ['GR', None],
  'HR': ['HR', None],
  'HU': ['HU', None],
  'IE': ['IE', None],
  'IM': ['GB', None],
  'IT': ['IT', None],
  'LT': ['LT', None],
  'LU': ['LU', None],
  'LV': ['LV', None],
  'MC': ['FR', None],
  'MT': ['MT', None],
  'NL': ['NL', None],
  'PL': ['PL', None],
  'PT': ['PT', None],
  'PT-20': ['PT', None],
  'PT-30': ['PT', None],
  'RO': ['RO', None],
  'SE': ['SE', None],
  'SI': ['SI', None],
  'SK': ['SK', None],
}

if __name__ == '__main__':
    price = BASE_PRICES['USD'][-1]
    for plan, slots in PLAN_SLOTS.items():
        total = slots * PLAN_FACTORS[plan] * price
        print "%10s  %s" % (plan, total)
