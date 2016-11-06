% if sent:
<div class="alert-green">You have been sent an email with an authorised link. Please check your email.</div>
% else:
% if error:
<div class="alert-red">${error|h}</div>
% endif
<div class="inner"><div class="content center pad-bottom">
	<br><br>
	% if existing:
	<div>Please click the button below to have an email with an authorised link sent to you. You can then use the link to update your details.</div>
	% else:
	<div>Please enter the email address that you used to set up your sponsorship:</div>
	% endif
	<br>
	<div class="form center">
		<form action="/login" method="POST">
			<input type="hidden" name="return_to" value="${return_to|h}">
			<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
			% if existing:
			<input type="hidden" name="email" value="${email|h}">
			% else:
			<input type="text" name="email" value="${email|h}" placeholder="you@yourdomain.com" autofocus>
			% endif
			<input type="submit" name="submit" value="Email Authorised Link">
		</form>
	</div>
</div></div>
% endif