<div class="content inner">
	<table class="users-list">
		<thead>
			<th>Name</th>
			<th>Email</th>
			<th>Profile</th>
			<th>Plan</th>
			<th>Info</th>
		</thead>
		% for user in users:
		<tr>
			<td class="constrained-width">${user.name|h}</td>
			<td class="constrained-width"><a href="mailto:${user.email|h}">${user.email|h}</a></td>
			<td class="constrained-width">
			% if user.sponsor and user.link_text:
				% if user.link_url:
				<a href="${user.link_url|h}">${user.link_text}</a>
				% else:
				${user.link_text}
				% endif
			% endif
			</td>
			<td>
				% if user.plan:
					% if user.stripe_subscription:
						% if ctx.LIVE:
						<a href="https://dashboard.stripe.com/subscriptions/${user.stripe_subscription}">${user.plan}</a>
						% else:
						<a href="https://dashboard.stripe.com/test/subscriptions/${user.stripe_subscription}">${user.plan}</a>
						% endif
					% else:
					${user.plan}
					% endif
					% if user.delinquent:
					<em>*delinquent</em>
					% endif
					% if user.stripe_is_unpaid:
					<em>*unpaid</em>
					% endif
				% endif
			</td>
			<td>
				% if ctx.ON_GOOGLE:
				<a href="https://console.cloud.google.com/datastore/entities/edit?key=0%2F%7C4%2FUser%7C19%2Fid:${user.key().id()}&project=gitfund&ns=&kind=User">edit</a>
				% else:
				<a href="http://localhost:8000/datastore/edit/${str(user.key())}">edit</a>
				% endif
				% if user.stripe_customer_id:
					·
					% if ctx.LIVE:
					<a href="https://dashboard.stripe.com/customers/${user.stripe_customer_id}">stripe</a>
					% else:
					<a href="https://dashboard.stripe.com/test/customers/${user.stripe_customer_id}">stripe</a>
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