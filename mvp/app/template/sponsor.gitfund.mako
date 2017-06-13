% if donated:
<div class="alert-green">Thank you for sponsoring GitFund!</div>
% else:
% if error:
<div class="alert-red">${error|h}</div>
% endif
% if error_html:
<div class="alert-red">${error_html}</div>
% endif
<div class="inner content">
	<div class="notice">
		Thank you for supporting GitFund.
		Your sponsorship will help make a real difference.
	</div>
	<form action="/sponsor.gitfund" method="POST" id="sponsor-form" class="dataform">
		<div class="field">
			<label for="sponsor-name">Sponsor Name</label>
			<div class="field-data">
				<input id="sponsor-name" class="field-input" name="name" value="${name|h}" autofocus>
				<div id="sponsor-name-error" class="field-errmsg"></div>
			</div>
		</div>
		<div class="field">
			<label for="sponsor-email">Email Address</label>
			<div class="field-data">
				<input id="sponsor-email" class="field-input" name="email" value="${email|h}" autocapitalize="none" autocorrect="off">
				<div id="sponsor-email-error" class="field-errmsg"></div>
			</div>
		</div>
		<div class="field">
			<label for="sponsor-plan">Sponsorship Tier</label>
			<div class="field-data">
				<div class="select-box"><select id="sponsor-plan" name="plan">
					% for tier in ['bronze', 'silver', 'gold', 'platinum']:
					<option${plan == tier and ' selected' or ''} value="${tier}" id="plan-${tier}">${ctx.PLANS[tier]}</option>
					% endfor
				</select></div>
			</div>
		</div>
		<div class="field">
			<label for="sponsor-territory">Country</label>
			<div class="field-data">
				<div class="select-box"><select id="sponsor-territory" name="territory">
				<option value="" style="display: none"></option>
				% for tset in ctx.TERRITORIES:
					% if len(tset) != 1:
					<optgroup label="${tset[-1][0]}">
					% endif
					% for territory_name, territory_code in tset:
					<option value="${territory_code}">${territory_name}</option>
					% endfor
					% if len(tset) != 1:
					</optgroup>
					% endif
				% endfor
				</select></div>
				<div id="sponsor-territory-error" class="field-errmsg"></div>
			</div>
		</div>
		<div class="field" id="sponsor-tax-id-field" style="display: none;">
			<label for="sponsor-tax-id">VAT ID</label>
			<div class="field-data">
				<input id="sponsor-tax-id" class="field-input" name="tax_id" value="${tax_id|h}" autocapitalize="none" autocorrect="off">
				<div id="sponsor-tax-id-error" class="field-errmsg"></div>
			</div>
		</div>
		% if not card:
		<div class="clear"></div>
		<h3>Card Details<div class="card-secure"><img src="${STATIC('gfx/secure.svg')}">Secure</div></h3>
		<div class="field">
			<label for="card-number">Card Number</label>
			<div class="field-data">
				<input id="card-number" class="field-input" type="tel">
				<div class="card-icons" id="card-icons">
					<img src="${STATIC('gfx/card.visa.png')}" id="card-visa">
					<img src="${STATIC('gfx/card.mastercard.png')}" id="card-mastercard">
					<img src="${STATIC('gfx/card.amex.png')}" id="card-amex">
				</div>
				<div id="card-number-error" class="field-errmsg"></div>
			</div>
		</div>
		<div class="field">
			<label for="card-exp-month">Expiration</label>
			<div class="field-data">
				<div class="select-box"><select id="card-exp-month">
					<option value="">MM</option>
					% for month in range(1, 13):
					<option value="${'%02d' % month}">${'%02d' % month}</option>
					% endfor
				</select></div>
				<div class="select-box"><select id="card-exp-year">
					<option value="">YY</option>
					<% 
						from datetime import datetime
						year_start = datetime.utcnow().year - 2000
					%>
					% for year in range(year_start, year_start+21):
					<option value="${year}">${year}</option>
					% endfor
				</select></div>
				<div id="card-exp-error" class="field-errmsg">Please provide the card expiry month.</div>
			</div>
		</div>
		<div class="field">
			<label for="card-cvc">Security Code</label>
			<div class="field-data">
				<input id="card-cvc" class="field-cvc" type="tel" maxlength="4">
				<div id="card-cvc-error" class="field-errmsg">Card security code must be present.</div>
			</div>
		</div>
		% endif
		<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
		<input id="card-token" type="hidden" name="card" value="${card|h}">
		<div class="field-submit">
			<p>By confirming your monthly sponsorship, you are agreeing to <a href="/site/terms">GitFund's Terms of Service</a> and <a href="/site/privacy">Privacy Policy</a>.</p>
			<input type="submit" value="Confirm Monthly Sponsorship">
		</div>
	</form>
</div>
<script>${ctx.FINANCE_JS}</script>
% endif