% if sent:
<div class="alert-green">You have been sent an invite. Please check your email.</div>
% else:
% if error:
<div class="alert-red">${error|h}</div>
% endif
<div class="inner"><div class="community-page content center">
	<div><img src="${STATIC('gfx/slack.png')}" width="128px"></div>
	<p>
		Join <a href="https://gitfund.slack.com/">GitFund</a> on Slack.
	</p>
	<div class="form">
		<form action="/community" method="POST">
			<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
			<input type="text" name="email" value="" placeholder="you@yourdomain.com" autofocus>
			<input type="submit" name="submit" value="Get My Invite">
		</form>
	</div>
	<p>Or <a href="https://gitfund.slack.com/">sign in</a>.</p>
	<div class="irc-info">
		<p>Or, if you prefer IRC, you can join us on:</p>
		<p><a href="irc://chat.freenode.net/esp">#esp on chat.freenode.net</a></p>
	</div>
</div></div>
% endif
