# Public Domain (-) 2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

from decimal import Decimal

EU_VAT_TERRITORIES = frozenset([
  'AT',
  'AT-JU',
  'AT-MI',
  'BE',
  'BG',
  'CY',
  'CZ',
  'DE',
  'DK',
  'EE',
  'EL',
  'ES',
  'FI',
  'FR',
  'GB',
  'GR',
  'GR-81',
  'GR-82',
  'GR-83',
  'GR-84',
  'GR-85',
  'GR-NS',
  'GR-ST',
  'HR',
  'HU',
  'IE',
  'IM',
  'IT',
  'LT',
  'LU',
  'LV',
  'MC',
  'MT',
  'NL',
  'PL',
  'PT',
  'PT-20',
  'PT-30',
  'RO',
  'SE',
  'SI',
  'SK',
])

PLAN_AMOUNTS = {
    'bronze': 750,
    'silver': 1500,
    'gold': 3000,
    'platinum': 6000
}

PLAN_SLOTS = {
    'bronze': 40,
    'silver': 20,
    'gold': 10,
    'platinum': 5
}

def _gen_plan_factors():
    factors = {}
    plans = PLAN_AMOUNTS.keys()
    total = 0
    for plan in plans:
        total += PLAN_AMOUNTS[plan] * PLAN_SLOTS[plan]
    total = Decimal(total)
    for plan in plans:
        factors[plan] = Decimal(PLAN_AMOUNTS[plan]) / total
    return factors

PLAN_FACTORS = _gen_plan_factors()
