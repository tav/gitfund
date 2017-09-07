<div class="inner"><div class="content">
<div class="notice-sponsors">
	GitFund is made possible thanks to the support of our generous donors and sponsors.
	% if not (ctx.user and ctx.user.backer):
	<a href="/back.gitfund?plan=donor">Become a donor today</a>.
	% endif
</div>
<div>
	<ul class="donors-list">
	% for donor in donors:
		<li>${donor.name|h}</li>
	% endfor
	</ul>
	<div class="clear"></div>
	% if cursor:
	<div class="cursor">
		<a href="/site.donors?cursor=${cursor}">More</a>
	</div>
	% endif
</div>
</div></div>
