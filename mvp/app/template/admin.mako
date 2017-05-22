% if error:
<div class="alert-red">${error|h}</div>
% endif
<div class="inner"><div class="content center">
	<br><br><br>
	<div class="form center">
		<form action="/admin" method="POST">
			<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
			<input type="password" name="key" value="" placeholder="Authorisation Key" autofocus>
			<input type="submit" name="submit" value="Enter">
		</form>
	</div>
	<br><br><br>
</div></div>
