<!doctype html>
<meta charset=utf-8>
<meta name="viewport" content="width=device-width">
% if ctx.site_title:
<title>${ctx.site_title|h}</title>
% else:
<title>${ctx.page_title and (u'%s · ' % ctx.page_title) or ''|h}GitFund</title>
% endif
<meta name="author" content="Espians">
% if ctx.site_description:
<meta name="description" content="${ctx.site_description|h}">
% if ctx.site_image:
<meta name="twitter:card" content="summary_large_image">
% else:
<meta name="twitter:card" content="summary">
% endif
% if ctx.site_title:
<meta name="twitter:title" content="${ctx.site_title|h}">
% elif ctx.page_title:
<meta name="twitter:title" content="${ctx.page_title|h} · GitFund">
% else:
<meta name="twitter:title" content="GitFund">
% endif
<meta name="twitter:description" content="${ctx.site_description|h}">
% endif
% if ctx.site_image:
<meta property="og:image" content="${ctx.site_image}">
<meta property="twitter:image" content="${ctx.site_image}">
<meta property="image-attribution" content="${ctx.site_image_attribution}">
% endif
% if ctx.noindex:
<meta name="robots" content="noindex">
% endif
<meta name="emoji-attribution" content="Emoji art provided by EmojiOne under CC-BY-4.0">
<link rel="icon" type="image/png" href="/favicon.ico?v=1">
<link rel="stylesheet" href="${STATIC('site.css')}">
<body>
<script src="${STATIC('site.js')}"></script>
% if ctx.stripe_js:
<script src="https://js.stripe.com/v2/"></script>
<script>
Stripe.setPublishableKey('${ctx.STRIPE_PUBLISHABLE_KEY}');
</script>
% endif
<div class="main">
<div class="header"><div class="inner">
	<div class="navicon"><div></div></div>
	<div class="navlinks">
		% if ctx.name != 'tav':
		<a href="/tav/gitfund">Home</a>
		% endif
		<a href="/site.sponsors">Sponsors</a>
		<a href="/community">Slack/IRC Community</a>
		% if ctx.user_id:
		<a href="/manage.sponsorship">Manage Sponsorship</a>
		<a href="/logout">Log Out</a>
		% else:
		<a href="/login">Log In</a>
		% endif
	</div>
	<div class="logo"><a href="/"><div class="logo-image"><div class="logo-image-dollar">$</div><div class="logo-image-pipe">&gt;</div></div><div class="logo-text">GitFund</div></a></div>
</div></div>
<div class="body">
${content}
</div>
% if ctx.show_sponsors_footer:
<% sponsors = ctx.get_site_sponsors() %>
% if sponsors:
<div id="sponsored-by" class="sponsored-by-heading"><div class="inner">
<h3>THANKS TO OUR SPONSORS:</h3>
</div></div>
<div class="sponsored-by-profiles"><div class="inner">
% for sponsor in sponsors:
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
</div></div>
% endif
% endif
</div>
<div class="footer"><div class="inner"><div class="footer-content">
<ul>
	<li>&copy; ${ctx.current_year()} Espians LLP</li>
	<li><a href="/site/about">About Us</a></li>
	<li><a href="/site/press">Press</a></li>
	<li><a href="/site.sponsors">Our Sponsors</a></li>
	<li><a href="/community">Slack/IRC Community</a></li>
	<li><a href="/sponsor.gitfund">Sponsor GitFund</a></li>
</ul>
<ul>
	<li>Support</li>
	<li><a href="/site/help">Common Issues</a></li>
	<li><a href="/site/privacy">Privacy Policy</a></li>
	<li><a href="/site/cookies">Cookie Policy</a></li>
	<li><a href="/site/terms">Terms of Service</a></li>
	<li><a href="/site/flo-statement">FLO Statement</a></li>
	<li><a href="/site/code-of-conduct">Code of Conduct</a></li>
	<li><a href="/site/security">Security Policy</a></li>
</ul>
<ul>
	<li>Follow Us</li>
	<li><a class="footer-facebook" href="https://www.facebook.com/gitfund">Facebook</a></li>
	<li><a class="footer-twitter" href="https://twitter.com/gitfund">Twitter</a></li>
</ul>
</div></div></div>
