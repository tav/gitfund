<div class="inner"><div class="content">
<div class="notice-sponsors">
	GitFund is made possible thanks to the support of our generous sponsors.
	<a href="/sponsor.gitfund">Become a sponsor today</a>.
</div>
% for tier in ['platinum', 'gold', 'silver', 'bronze']:
<% tier_sponsors = sponsors[tier] %>
% if tier_sponsors:
<div class="sponsor-tier-heading">${tier.upper()} SPONSORS</div>
<div class="sponsor-tier">
% for sponsor in tier_sponsors:
	<div class="sponsor-image">
	% if sponsor['url']:
		<a href="${sponsor['url']|h}"><img src="${ctx.get_sponsor_image_url(sponsor, '300')}"></a>
	% else:
		<img src="${ctx.get_sponsor_image_url(sponsor, '300')}">
	% endif
	</div>
% endfor
</div>
<div class="clear"></div>
% endif
% endfor
</div></div>
