% if ctx.user.sponsor:
<div class="inner"><div class="content pad-bottom">
<h1>Manage Sponsorship</h1>
<ul>
	<li><p><a href="/update.sponsor.profile">Update Your Sponsor Profile</a></p></li>
	<li><p><a href="/sponsor.gitfund">Update Billing Details</a></p></li>
	<li><p><a href="/cancel.sponsorship">Cancel Sponsorship</a></p></li>
</ul>
</div></div>
% else:
<div class="alert-red">Sorry, there are no active sponsorships on this account at the moment.</div>
% endif
