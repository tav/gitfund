<div class="campaign">
<div class="campaign-header">
	<div class="campaign-banner"><div class="inner">
		<div class="info"><a href="/site.sponsors"><strong>${"{:,}".format(totals.sponsor_count)}</strong> ${ctx.pluralise('sponsor', totals.sponsor_count)}</a></div>
		<div class="info" id="footnote-1-backref"><a href="/site.sponsors"><strong>£${"{:,}".format(0)}</strong> per month<a href="#footnote-1"><sup>*</sup></a></a></div>
		<a class="sponsor" href="/sponsor.gitfund">Back This Project</a>
	</div></div>
</div>
<div class="clear"></div>
<div class="campaign-cols"><div class="campaign-inner">
	% if ctx.preview_mode:
	<div class="preview-warn">This is for preview only. Please do not share publicly. Thank you.</div>
	% endif
	<div class="project-title inner-pad-only">${ctx.CAMPAIGN_TITLE|h}</div>
	<div class="inner-pad-only">
		<a class="button-twitter" href="https://twitter.com/intent/tweet/?${ctx.urlencode({'text': 'Check out ' + ctx.site_title.encode('utf-8'), 'url': 'https://gitfund.io/tav/gitfund'})}"><span>Tweet</span></a>
		<a class="button-facebook" href="https://facebook.com/sharer/sharer.php?${ctx.urlencode({'u': 'https://gitfund.io/tav/gitfund'})}"><span>Share</span></a>
		<a class="ghb" href="https://github.com/tav/gitfund"><span class="ghb-left"><span class="ghb-icon"></span><span class="ghb-repo">gitfund</span></span><span class="ghb-right"><span class="ghb-star"></span><span class="ghb-count">${social.repo.stars}</span></span></a>
		<a href="#disqus_thread" data-disqus-identifier="tav/gitfund" id="disqus_count" class="comment-link">Leave a comment</a>
	</div>
	<div class="campaign-col1">
		<div class="campaign-box campaign-content content">
			${ctx.CAMPAIGN_CONTENT}
		</div>
		<div class="inner-pad-only"><div class="disqus">
			<div id="disqus_thread"></div>
		</div></div>
		<div class="inner-pad-only">
			<p id="footnote-1">
				<small><a href="#footnote-1-backref">*</a>
				This is an approximate of the total raised — excluding sales taxes
				and Stripe fees. It will vary over time as currency exchange rates
				fluctuate.</small>
			</p>
		</div>
	</div>
	<div class="campaign-col2">
		<div class="campaign-box">
			<div class="campaign-box-inner-sides">
			<div class="goal-bar"><div style="width: ${totals.percentage}%"></div></div>
			% for idx, (target, description, reached) in enumerate(reversed(totals.goals)):
			<div class="goal">
				% if reached:
				<div class="goal-status">Goal: ${target}% <span>&nbsp;—&nbsp; reached!</span></div>
				% elif target == 100:
				<div class="goal-status">Goal: 100%</div>
				% else:
				<div class="goal-status">Goal: ${target}% of total</div>
				% endif
				<div class="content${idx != (len(totals.goals) - 1) and ' campaign-box-divider' or ''}">${description}</div>
			</div>
			% endfor
			</div>
		</div>
		<div class="campaign-box">
			<div class="campaign-box-title">SPONSOR</div>
			<div class="campaign-box-inner">
			<% territory_prices, territory_tax = pricing.basic[user_territory] %>
			% for idx, plan in enumerate(['bronze', 'silver', 'gold', 'platinum']):
				<%
					slots_taken = 0
					slots_total = ctx.PLAN_SLOTS[plan]
					slots_available = slots_total - slots_taken
					plan_title = plan.title()
					if slots_taken == slots_total:
						remaining = 'All %s slots taken' % slots_total
					elif not slots_taken:
						remaining = '%s slots available' % slots_available
					else:
						remaining = '%s of %s slots available' % (slots_available, slots_total)
				%>
				<div class="backing-plan-title">${plan_title} Sponsorship</div>
				<div class="backing-plan-backers">${remaining}, <span id="basic-price-${idx}">${territory_prices[idx]}</span> / month</div>
				<div class="backing-plan-desc content">${ctx.PLAN_DESCRIPTIONS[plan]}</div>
				<div class="backing-plan-select${plan != 'bronze' and ' campaign-box-divider' or ''}"><a href="/sponsor.gitfund?plan=${plan}">Become a ${plan_title} Sponsor</a></div>
			% endfor
			</div>
		</div>
		<div class="campaign-box">
		<div class="campaign-box-inner">
			Prices shown for:
			<select id="update-basic-prices">
			% for tset in ctx.TERRITORIES:
				% if len(tset) != 1:
				<optgroup label="${tset[-1][0]}">
				% endif
				% for territory_name, territory_code in tset:
				<option value="${territory_code}"${territory_code == user_territory and ' selected="selected"' or ''}>${territory_name}</option>
				% endfor
				% if len(tset) != 1:
				</optgroup>
				% endif
			% endfor
			</select>
		</div>
		</div>
		<div class="campaign-box">
			<div class="campaign-box-title">CORE TEAM</div>
			<div class="campaign-box-inner">
			% for idx, profile in enumerate(ctx.CAMPAIGN_TEAM):
				<%
					github = social.github.get(profile.github, None)
					twitter = social.twitter.get(profile.twitter, None)
				%>
				<div class="team-profile-name">${profile.name|h}</div>
				% if profile.main == 'twitter':
				<div class="team-profile-image"><img src="${twitter.avatar.replace('_normal', '')}"></div>
				<div class="team-profile-bio content">${ctx.linkify_twitter_bio(twitter.description)}</div>
				% elif profile.main == 'github':
				<div class="team-profile-image"><img src="${github.avatar}"></div>
				<div class="team-profile-bio content">${ctx.linkify_github_bio(github.description)}</div>
				% endif
				<div class="team-profile-follow${idx != (len(ctx.CAMPAIGN_TEAM) - 1) and ' campaign-box-divider' or ''}">
				% if profile.twitter:
					<a href="https://twitter.com/intent/follow?screen_name=${profile.twitter}"><span class="team-profile-icon team-profile-twitter"></span><span class="team-profile-follow-username">Follow @${profile.twitter}</span><span class="team-profile-follow-count">${format(twitter.followers, ",d")} followers</span></a>
				% endif
				% if profile.github:
					<a href="https://github.com/${profile.github}"><span class="team-profile-icon team-profile-github"></span><span class="team-profile-follow-username">Follow @${profile.github}</span><span class="team-profile-follow-count">${format(github.followers, ",d")} followers</span></a>
				% endif
				% if profile.linkedin:
					<a href="https://www.linkedin.com/in/${profile.linkedin[0]}/"><span class="team-profile-icon team-profile-linkedin"></span><span class="team-profile-follow-username">Connect with ${profile.name.split()[0]}</span><span class="team-profile-follow-count">${profile.linkedin[1]} connections</span></a>
				% endif
				</div>
			% endfor
			</div>
		</div>
		<div class="campaign-box">
			<div class="campaign-box-title">SHARE</div>
			<div class="campaign-box-inner-sides">
				<a class="share share-facebook" href="https://facebook.com/sharer/sharer.php?${ctx.urlencode({'u': 'https://gitfund.io/tav/gitfund'})}"><div>Share on Facebook</div></a>
				<a class="share share-twitter" href="https://twitter.com/intent/tweet/?${ctx.urlencode({'text': 'Check out ' + ctx.site_title.encode('utf-8'), 'url': 'https://gitfund.io/tav/gitfund'})}"><div>Share on Twitter</div></a>
				<a class="share share-email" href="mailto:?${ctx.urlencode({'subject': ctx.site_title.encode('utf-8'), 'body': 'Check out https://gitfund.io/tav/gitfund'})}"><div>Share via Email</div></a>
			</div>
		</div>
	</div>
	<div class="fix-layout">&nbsp;</div>
</div></div>
<div class="clear"></div>
</div>
<script>${pricing.basic_js}</script>
