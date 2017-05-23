<div class="content inner">
	<table class="users-list">
		<thead>
			<th>Name</th>
			<th>Email</th>
			<th>Company</th>
			<th>Plan</th>
			<th>Info</th>
		</thead>
		% for user in users:
		<tr>
			<td class="constrained-width">${user.name|h}</td>
			<td class="constrained-width"><a href="mailto:${user.email|h}">${user.email|h}</a></td>
			<td class="constrained-width">${user.company|h}</td>
			<td>
				% if user.plan:
				${user.plan}${user.delinquent and '<span>*</span>' or ''}
				% else:
				${user.status}
				% endif
			</td>
			<td>
				% if ctx.ON_GOOGLE:
				<a href="https://console.cloud.google.com/datastore/entities/edit?key=0%2F%7C1%2FU%7C19%2Fid:${user.key().id()}&project=gitfund&ns=&kind=U">edit</a>
				% else:
				<a href="http://localhost:8000/datastore/edit/${str(user.key())}">edit</a>
				% endif
				% if user.stripe_id:
					·
					% if LIVE:
					<a href="https://dashboard.stripe.com/customers/${user.stripe_id}">stripe</a>
					% else:
					<a href="https://dashboard.stripe.com/test/customers/${user.stripe_id}">stripe</a>
					% endif
				% endif
			</td>
		</tr>
		% endfor
	</table>
	<div class="cursor">
		% if cursor:
		<a href="/users.list?cursor=${cursor}">More</a>
		% endif
	</div>
</div>