% if created:
<div class="alert-green">Thank you. The sponsor has been created.</div>
% else:
% if error:
<div class="alert-red">${error|h}</div>
% endif
<div class="inner"><div class="content pad-bottom">
	<h1>Add Manual Sponsor</h1>
	<br>
	<form action="/manual.sponsor" method="POST" enctype="multipart/form-data" class="dataform">
		<input type="hidden" name="xsrf" value="${ctx.xsrf_token}">
		<div class="field">
			<label for="name">Name</label>
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
			<label for="plan">Support Tier</label>
			<div class="field-data">
				<div class="select-box"><select id="plan" name="plan">
					% for tier in ['donor', 'bronze', 'silver', 'gold', 'platinum']:
					<option${plan == tier and ' selected' or ''} value="${tier}">${tier.title()}</option>
					% endfor
				</select></div>
			</div>
		</div>
		<div class="field">
			<label for="link">Link</label>
			<div class="field-data">
				<input id="link" class="field-input" name="link" value="${link|h}">
			</div>
		</div>
		<div class="field">
			<label for="image">Image</label>
			<div class="field-data">
				<input id="image" type="file" class="field-input" name="image" value="">
			</div>
		</div>
		<div class="field-submit">
			<input type="submit" class="submit-button" value="Add Sponsor">
		</div>
	</form>
</div></div>
% endif