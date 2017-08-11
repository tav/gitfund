% if error:
<div class="alert-red">${error|h}</div>
% elif cancelled:
<div class="alert-green">Your subscription has now been cancelled. Thank you for your support!</div>
% else:
<div class="inner"><div class="content center pad-bottom">
	<br><br>
	<p>
		Are you sure you want to cancel the ${backer.plan.title()} subscription from ${backer.email|h}?
	</p>
	<br>
	<div class="form center">
		<form action="/cancel.subscription" method="POST">
			<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
			<input type="submit" name="submit" value="Cancel Subscription">
		</form>
	</div>
</div></div>
% endif