% if error:
<div class="alert-red">${error|h}</div>
% elif setup:
<div class="alert-green">Thank you for sponsoring GitFund! You can now set up your sponsor profile.</div>
% endif
<div class="inner"><div class="content">
<h1>Update Your Sponsor Profile</h1>
<p>
	Please make sure your details are in line with our
	<a href="/site/terms">Terms of Service</a>, especially the
	<a href="/site/terms#sponsor-profile">Sponsor Profile</a> section.
</p>
<br>
<form action="/update.sponsor.profile" method="POST" enctype="multipart/form-data" class="dataform">
	<div class="field">
		<label for="link_text">Link Text</label>
		<div class="field-data">
			<input class="field-input" id="link_text" name="link_text" value="${link_text|h}" placeholder="Your name or company name" autofocus>
		</div>
	</div>
	<div class="field">
		<label for="link_url">Link URL</label>
		<div class="field-data">
			<input class="field-input" id="link_url" name="link_url" value="${link_url|h}" placeholder="https://yoursite.com">
		</div>
	</div>
	<div class="field">
		<label for="image">Sponsor Image</label>
		<div class="field-data">
			<input type="file" class="field-input" id="image" name="image" value="">
		</div>
	</div>
	<div class="field-submit">
		<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
		<input type="submit" value="Update Sponsor Profile">
	</div>
</form>
</div></div>
