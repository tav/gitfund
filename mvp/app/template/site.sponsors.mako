% if thanks:
<div class="alert-green">Your sponsor profile is being updated. Thank you for your support!</div>
% endif
<div class="inner"><div class="content">
<div class="notice-sponsors">
	GitFund is made possible thanks to the support of our generous donors and sponsors.
	% if not (ctx.user and ctx.user.backer):
	<a href="/back.gitfund?plan=bronze">Become a sponsor today</a>.
	% endif
</div>
% for tier in ['platinum', 'gold', 'silver', 'bronze']:
<% tier_sponsors = sponsors[tier] %>
% if tier_sponsors:
<div class="sponsor-tier-heading">${tier.upper()} SPONSORS</div>
<br>
<div class="sponsor-tier">
% for sponsor in tier_sponsors:
	<div class="sponsor-profile">
		<div class="sponsor-image">
		% if sponsor['url']:
			<a href="${sponsor['url']|h}"><img src="${ctx.get_sponsor_image_url(sponsor, '300')}"></a>
		% else:
			<img src="${ctx.get_sponsor_image_url(sponsor, '300')}">
		% endif
		</div>
		% if sponsor['text']:
		<div class="sponsor-link">
			% if sponsor['url']:
			<a href="${sponsor['url']|h}">${sponsor['text']|h}</a>
			% else:
			${sponsor['text']|h}
			% endif
		</div>
		% endif
	</div>
% endfor
	<div class="clear"></div>
</div>
<div class="clear"></div>
% endif
% endfor
</div></div>
