# Public Domain (-) 2016-2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

from datetime import datetime
from decimal import Decimal

# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------

PLAN_FACTORS = [('bronze', 1), ('silver', 5), ('gold', 50), ('platinum', 100)]

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
# Ignoring currencies which create amounts greater than the maximum chargeable
# amount on Stripe of 99999999, e.g.
#
#     'CLP': [88000],
#     'COP': [420000],
#     'HUF': [36000],
#     'IDR': [1800000],
#     'IRR': [4000000],
#     'LKR': [19000],
#     'PKR': [13100],
#     'RSD': [15000],
#     'VND': [2800000],
#
# And currencies which are not supported on Stripe, e.g.
#
#     Bahraini Dinar (BHD), pegged at 1 USD == 0.376 BHD
#     Belarusian Ruble (BYR)
#     Bhutanese Ngultrum (BTN), pegged 1:1 to INR
#     Kuwaiti Dinar (KWD), pegged to USD
#     Manx Pound (IMP), pegged 1:1 to GBP
#     Venezuelan Boliva (VEF)
#
# And currencies with major discrepancies between official and black market
# rates, e.g.
#
#     Nigerian Naira (NGN)
#
BASE_PRICES = {
    'AED': [440],    # Pegged @ 1 USD == 3.6725 AED
    'ARS': [2000],
    'AUD': [180],
    'BDT': [9900],
    'BGN': [230],
    'BRL': [500],
    'CAD': [180],
    'CHF': [130],
    'CNY': [840],
    'CZK': [3200],
    'DKK': [860],
    'EGP': [2400],
    'EUR': [120],
    'GBP': [100],
    'HKD': [940],    # Pegged to USD
    'HRK': [880],
    'ILS': [480],
    'INR': [8300],
    'JPY': [15000],
    'KRW': [150000],
    'MAD': [1300],
    'MXN': [2700],
    'MYR': [540],
    'NOK': [1080],
    'NZD': [190],
    'PEN': [420],
    'PHP': [6100],
    'PLN': [520],
    'RON': [540],
    'RUB': [9900],
    'SAR': [450],    # Pegged @ 1 USD == 3.75 SAR
    'SEK': [1200],
    'SGD': [180],
    'THB': [4400],
    'TRY': [470],
    'TWD': [4100],
    'UAH': [3400],
    'USD': [120],
    'ZAR': [2100],
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
# Tax Regimes
# -----------------------------------------------------------------------------

UK_VAT = 1
EU_VAT = 2

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
# Tax Specs
# -----------------------------------------------------------------------------

class TaxSpec(object):
    def __init__(
        self, type, rate, id_prefix='', normalize_id=None,
        start=datetime(2000, 1, 1, 0, 0, 0),
        ):
        self.id_prefix = id_prefix
        self.normalize_id = normalize_id
        self.rate = Decimal(rate)
        self.start = start
        self.type = type

def set_eu_vat(
    territory, rate, normalize_id=None, id_prefix='',
    start=datetime(2000, 1, 1, 0, 0, 0)
    ):
    if territory not in TERRITORY2TAX:
        TERRITORY2TAX[territory] = []
    if not id_prefix:
        id_prefix = territory.split('-')[0]
    TERRITORY2TAX[territory].append(TaxSpec(
        EU_VAT, rate, id_prefix, normalize_id, start
    ))

TERRITORY2TAX = {
    'GB': [TaxSpec(UK_VAT, '20', 'GB')],
}

# EU VAT rates are informed by:
# http://ec.europa.eu/taxation_customs/sites/taxation/files/resources/documents/taxation/vat/how_vat_works/rates/vat_rates_en.pdf
#
# Documents on the EU website contradict each other in relation to VAT rates in
# certain territories, e.g.
#
# * The French Overseas Departments (DOM) are stated as not being part of
#   Community territory for the purposes of VAT, but are also described as
#   having a standard rate of 8.5% as being applicable. Is that local VAT or EU
#   VAT?
#
set_eu_vat('AT', '20', handle_austrian_vat_id)
set_eu_vat('AT-JU', '19', handle_austrian_vat_id)
set_eu_vat('AT-MI', '19', handle_austrian_vat_id)
set_eu_vat('BE', '21', handle_belgian_vat_id)
set_eu_vat('BG', '20')
set_eu_vat('CY', '19')
set_eu_vat('CZ', '21')
set_eu_vat('DE', '19')
set_eu_vat('DK', '25')
set_eu_vat('EE', '20')
set_eu_vat('EL', '24')
set_eu_vat('ES', '21')
set_eu_vat('FI', '24')
set_eu_vat('FR', '20')
set_eu_vat('GR', '24')
set_eu_vat('GR-83', '17')
set_eu_vat('HR', '25')
set_eu_vat('HU', '27')
set_eu_vat('IE', '23')
set_eu_vat('IT', '22')
set_eu_vat('LT', '21')
set_eu_vat('LU', '17')
set_eu_vat('LV', '21')
set_eu_vat('MT', '18')
set_eu_vat('NL', '21')
set_eu_vat('PL', '23')
set_eu_vat('PT', '23')
set_eu_vat('PT-20', '18')
set_eu_vat('PT-30', '22')
set_eu_vat('RO', '19')
set_eu_vat('SE', '25')
set_eu_vat('SI', '22')
set_eu_vat('SK', '20')

# Alias shared VAT domains.
TERRITORY2TAX['GR-81'] = TERRITORY2TAX['GR-83']
TERRITORY2TAX['GR-82'] = TERRITORY2TAX['GR-83']
TERRITORY2TAX['GR-84'] = TERRITORY2TAX['GR-83']
TERRITORY2TAX['GR-85'] = TERRITORY2TAX['GR-83']
TERRITORY2TAX['GR-NS'] = TERRITORY2TAX['GR-83']
TERRITORY2TAX['GR-ST'] = TERRITORY2TAX['GR-83']
TERRITORY2TAX['IM'] = TERRITORY2TAX['GB']
TERRITORY2TAX['MC'] = TERRITORY2TAX['FR']

# -----------------------------------------------------------------------------
# Misc. Globals
# -----------------------------------------------------------------------------

DISPLAY_WITH_TAX = frozenset([
    UK_VAT
])

TAX_NOTICES = {
    EU_VAT: "Please note that all amounts are exclusive of any applicable VAT.",
    UK_VAT: "Please note that all amounts include %s%% VAT." % TERRITORY2TAX['GB'][-1].rate
}

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def get_tax_spec(territory, now):
    if territory not in TERRITORY2TAX:
        return
    rates = TERRITORY2TAX[territory]
    found = None
    for rate in rates:
        # TODO(tav): Should this take territory-specific time zones into
        # consideration for when new rates come into force?
        if now < rate.start:
            break
        found = rate
    return found
