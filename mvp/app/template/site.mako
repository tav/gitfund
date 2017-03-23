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
% endif
% if ctx.site_image:
<meta property="og:image" content="${ctx.site_image}">
% endif
% if ctx.noindex:
<meta name="robots" content="noindex">
% endif
<meta name="emoji-attribution" content="Emoji art provided by EmojiOne under CC-BY-4.0">
<link rel="icon" type="image/png" href="/favicon.ico?v=1">
<link rel="stylesheet" href="${STATIC('site.css')}">
<link rel="stylesheet" href="//fonts.googleapis.com/css?family=Source+Code+Pro:200,400|Open+Sans:300,400,700">
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
	<div class="navicon"><img src="${STATIC('gfx/menu.icon.svg')}"></div>
	<div class="navlinks">
		<a href="/site.sponsors">Sponsors</a>
		<a href="/community">Slack/IRC Community</a>
		% if ctx.user_id:
		<a href="/logout">Log Out</a>
		% endif
	</div>
	<div class="logo"><a href="/"><div class="logo-image"><div class="logo-image-dollar">$</div><div class="logo-image-pipe">&gt;</div></div><div class="logo-text">GitFund</div></a></div>
</div></div>
<div class="body">
${content}
</div>
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
	<li><a href="/site/code-of-conduct">Code of Conduct</a></li>
</ul>
<ul>
	<li>Follow Us</li>
	<li><a href="https://www.facebook.com/gitfund"><img src="${STATIC('gfx/facebook.grey.svg')}" style="margin-top: -8px; margin-left: -4px; margin-right: 8px">Facebook</a></li>
	<li><a href="https://twitter.com/gitfund"><img src="${STATIC('gfx/twitter.grey.svg')}" style="margin-left: -2px; margin-right: 2px">Twitter</a></li>
</ul>
</div></div></div>