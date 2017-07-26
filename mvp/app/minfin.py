# Public Domain (-) 2017 The GitFund Authors.
# See the GitFund UNLICENSE file for details.

from decimal import Decimal

CAMPAIGN_TARGET = Decimal(60000)

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

# -----------------------------------------------------------------------------
# Sponsorship Plan Spec
# -----------------------------------------------------------------------------

PLAN_AMOUNTS = {
    'donor': 12,
    'bronze': 1500,
    'silver': 3000,
    'gold': 6000,
    'platinum': 12000
}

PLAN_AMOUNTS_GB = {
  plan: (plan == 'donor' and amount or int(amount * 1.2))
  for plan, amount in PLAN_AMOUNTS.iteritems()
}

PLAN_FACTORS = {
  plan: amount / CAMPAIGN_TARGET
  for plan, amount in PLAN_AMOUNTS.iteritems()
}

PLAN_SLOTS = {
    'bronze': 40,
    'silver': 20,
    'gold': 10,
    'platinum': 5
}

PLAN_VERSION = 1

if __name__ == '__main__':
    for id, spec in [('std', PLAN_AMOUNTS), ('gb', PLAN_AMOUNTS_GB)]:
        print "%s:" % id
        for plan, amount in sorted(spec.items(), key=lambda x: x[1]):
            if plan in PLAN_SLOTS:
                print "%12s\t%s" % (plan, PLAN_SLOTS[plan] * amount)
        print
