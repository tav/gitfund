# -*- coding: utf-8 -*-

# Public Domain (-) 2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

import re
import sys

from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'app'))
sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'app', 'lib'))

from currency import TERRITORY2CURRENCY
from finance import (
    BASE_PRICES, CONTENT_FACTORS, PLAN_FACTORS, TERRITORY2TAX,
    ZERO_DECIMAL_CURRENCIES
)

INDEX = []
INDEX_JS = []
PLANS = {}
PRICES = {}
PRICES_JS = {}
PRICES_POS = {}
PRICES_JS_POS = {}

pos = pos_js = 0
seen = {}
segments = []
tiers = []
usd_base_price = BASE_PRICES['USD'][-1]
usd_version = len(BASE_PRICES['USD'])

replace_dollar_prefix = re.compile('[A-Z][A-Z]').sub

for plan, factor in sorted(PLAN_FACTORS.items(), key=lambda x: x[1]):
    PRICES_POS[plan + '-plain'] = pos
    PRICES_POS[plan + '-detailed'] = pos + 1
    PRICES_POS[plan + '-plan-id'] = pos + 2
    pos += 3
    PRICES_JS_POS[plan + '-plain'] = pos_js
    PRICES_JS_POS[plan + '-detailed'] = pos_js + 1
    pos_js += 2
    tiers.append((plan, factor))

for segment, factor in sorted(CONTENT_FACTORS.items(), key=lambda x: x[1]):
    PRICES_POS[segment] = pos
    PRICES_JS_POS[segment] = pos_js
    pos += 1
    pos_js += 1
    segments.append((segment, factor))

DETAILED_DEFAULT = [None] * pos
DETAILED_DEFAULT_JS = [None] * pos_js
for plan, _ in tiers:
    if plan == 'donor':
        title = 'Individual Donor'
    else:
        title = '%s Sponsor' % plan.title()
    DETAILED_DEFAULT[PRICES_POS[plan + '-detailed']] = title
    DETAILED_DEFAULT_JS[PRICES_JS_POS[plan + '-detailed']] = title

for territory in sorted(TERRITORY2CURRENCY):
    if territory in TERRITORY2TAX and TERRITORY2TAX[territory][0] == 'GB':
        gb_vat_regime = True
    else:
        gb_vat_regime = False
    fmt = TERRITORY2CURRENCY[territory]
    key = (fmt, gb_vat_regime)
    if key in seen:
        PRICES[territory], PRICES_JS[territory] = seen[key]
    else:
        currency = fmt.currency
        is_zero_decimal = currency in ZERO_DECIMAL_CURRENCIES
        currency_prices = BASE_PRICES[currency]
        base_price = currency_prices[-1]
        version = len(currency_prices)
        spec = []; append = spec.append
        spec_js = []; append_js = spec_js.append
        for plan, factor in tiers:
            amount = base_price * factor
            if gb_vat_regime and plan != 'donor':
                amount = int(1.2 * amount)
            usd = False
            if is_zero_decimal:
                if amount > 99999999:
                    amount = usd_base_price * factor
                    usd = True
            else:
                if amount > 999999:
                    amount = usd_base_price * factor
                    usd = True
            fmt_amount = fmt.format(str(amount), usd=usd)
            append(fmt_amount)
            append_js(fmt_amount)
            suffix = u' / month'
            if plan == 'donor':
                prefix = u'Individual Donor &nbsp;·&nbsp; '
                title = 'Individual Donor'
            else:
                prefix = u'%s Sponsor &nbsp;·&nbsp; ' % plan.title()
                title = '%s Sponsor' % plan.title()
                if gb_vat_regime:
                    suffix = u' / month (includes 20% VAT)'
            detailed_repr = u'%s%s%s' % (prefix, fmt_amount, suffix)
            append(detailed_repr)
            append_js(detailed_repr)
            if usd:
                plan_id = '%s.usd.v%d' % (plan, usd_version)
                plan_spec = (
                    amount * 100, 'USD', '%s USD v%d' % (title, usd_version)
                )
            else:
                plan_id = '%s.%s.v%d' % (plan, currency.lower(), version)
                title = '%s %s v%d' % (title, currency, version)
                if gb_vat_regime and plan != 'donor':
                    plan_id += '.vat'
                    title += ' with VAT'
                if is_zero_decimal:
                    plan_spec = (amount, currency, title)
                else:
                    plan_spec = (amount * 100, currency, title)
            if plan_id in PLANS and PLANS[plan_id] != plan_spec:
                print (
                    "ERROR: plan id %r spec %r does not match existing: %r"
                    % (plan_id, plan_spec, PLANS[plan_id])
                )
            PLANS[plan_id] = plan_spec
            append(plan_id)
        separator_uses_space = False
        for segment, factor in segments:
            amount = fmt.format(str(base_price * factor))
            if amount.startswith(u'GB'):
                amount = amount.replace(u'GB£\xa0', u'£')
            append(amount)
            append_js(amount)
        index_pos = len(INDEX)
        INDEX.append(spec)
        index_js_pos = len(INDEX_JS)
        INDEX_JS.append(spec_js)
        seen[key] = index_pos, index_js_pos
        PRICES[territory] = index_pos
        PRICES_JS[territory] = index_js_pos
