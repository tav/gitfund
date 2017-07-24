% if error:
<div class="alert-red">${error|h}</div>
% elif cancelled:
<div class="alert-green">Your sponsorship has now been cancelled. Thank you for your support!</div>
% else:
<div class="inner"><div class="content center pad-bottom">
	<br><br>
	<p>
		Are you sure you want to cancel the ${sponsor.plan.title()} sponsorship from ${sponsor.email|h}?
	</p>
	<br>
	<div class="form center">
		<form action="/cancel.sponsorship" method="POST">
			<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
			<input type="submit" name="submit" value="Cancel Sponsorship">
		</form>
	</div>
</div></div>
% endif