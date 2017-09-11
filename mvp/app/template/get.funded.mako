% if updated:
<div class="alert-green">Thank you. Your details have been saved.</div>
% else:
% if error:
<div class="alert-red">${error|h}</div>
% endif
<div class="inner"><div class="content pad-bottom">
	<h1>Get Funded</h1>
	<p>If you'd like your project to be part of the Beta launch of GitFund, then please submit your details below. We'll then get in touch before the launch.</p>
	<p>We welcome established projects like <a href="http://pypy.org/">PyPy</a>, as well as totally new projects.</p>
	<br><br>
	<form action="/get.funded" method="POST" class="dataform">
		<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
		<div class="field">
			<label for="name">Your Name</label>
			<div class="field-data">
				<input id="name" class="field-input" name="name" value="${name|h}">
			</div>
		</div>
		<div class="field">
			<label for="email">Email</label>
			<div class="field-data">
				<input id="email" class="field-input" name="email" value="${email|h}">
			</div>
		</div>
		<div class="field">
			<label for="url">Project/Repo URL</label>
			<div class="field-data">
				<input id="url" class="field-input" name="url" value="${url|h}">
			</div>
		</div>
		<div class="field-submit">
			<input type="submit" class="submit-button" value="Submit Project">
		</div>
	</form>
</div></div>
% endif