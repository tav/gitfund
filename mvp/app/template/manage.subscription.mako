<div class="inner"><div class="content pad-bottom">
<h1>Manage Subscription</h1>
<ul>
% if ctx.user.backer:
	% if ctx.user.sponsor:
	<li><p><a href="/update.sponsor.profile">Update Your Sponsor Profile</a></p></li>
	% endif
	<li><p><a href="/back.gitfund">Update Billing Details</a></p></li>
	<li><p><a href="/cancel.subscription">Cancel Subscription</a></p></li>
% else:
	<li><p><a href="/back.gitfund">Back GitFund</a></p></li>
% endif
</ul>
</div></div>
