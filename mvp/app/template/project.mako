<div class="campaign">
<div class="campaign-header">
	<div class="campaign-banner"><div class="inner">
		<div class="info"><a href="/site.sponsors"><strong>${"{:,}".format(totals.sponsors)}</strong> ${ctx.pluralise('sponsor', totals.sponsors)}</a></div>
		<div class="info"><a href="/site.sponsors"><strong>£${"{:,}".format(totals.raised)}</strong> per month</a></div>
		<a class="sponsor" href="/sponsor.gitfund">Back This Project</a>
	</div></div>
</div>
<div class="clear"></div>
<div class="campaign-cols"><div class="campaign-inner">
	% if thanks:
	<div class="alert-green">Your sponsor profile has been updated. Thank you for your support!</div>
	% elif ctx.preview_mode:
	<div class="preview-warn">This is for preview only. Please do not share publicly. Thank you.</div>
	% endif
	<div class="project-title inner-pad-only">${ctx.CAMPAIGN_TITLE|h}</div>
	<div class="inner-pad-only project-activity-bar">
		<a class="button-twitter" href="https://twitter.com/intent/tweet/?${ctx.urlencode({'text': 'Check out ' + ctx.site_title.encode('utf-8'), 'url': 'https://gitfund.io/tav/gitfund'})}"><span>Tweet</span></a>
		<a class="button-facebook" href="https://facebook.com/sharer/sharer.php?${ctx.urlencode({'u': 'https://gitfund.io/tav/gitfund'})}"><span>Share</span></a>
		<br>
		<a class="ghb" href="https://github.com/tav/gitfund"><span class="ghb-left"><span class="ghb-icon"></span><span class="ghb-repo">gitfund</span></span><span class="ghb-right"><span class="ghb-star"></span><span class="ghb-count">${social.repo.stars}</span></span></a>
		<a href="#disqus_thread" data-disqus-identifier="tav/gitfund" id="disqus_count" class="comment-link">Leave a comment</a>
	</div>
	<div class="campaign-col1">
		<div class="campaign-box campaign-content content inner-pad-only">
			${ctx.CAMPAIGN_CONTENT}
		</div>
		<div class="inner-pad-only comments-container"><div class="disqus more-block">
			<div id="disqus_thread"></div>
		</div></div>
	</div>
	<div class="campaign-col2">
		<div class="campaign-box">
			<div class="campaign-box-inner-sides">
			<div class="goal-bar"><div style="width: ${totals.percent}"></div></div>
			<div class="goal">
				% if totals.progress:
				<div class="goal-status">${totals.progress}</div>
				% endif
				<div class="content">${ctx.CAMPAIGN_GOAL}</div>
			</div>
			</div>
		</div>
		<div class="campaign-box">
			<div class="campaign-box-inner">
			% for idx, plan in enumerate(['bronze', 'silver', 'gold', 'platinum']):
				<%
					plan_title = plan.title()
					slots_total = ctx.PLAN_SLOTS[plan]
					slots_available = max(slots_total - totals.plans[plan], 0)
					if not slots_available:
						remaining = 'All %s slots taken' % slots_total
					elif slots_available == slots_total:
						remaining = '%s slots available' % slots_available
					else:
						remaining = '%s of %s slots available' % (slots_available, slots_total)
				%>
				<div class="backing-plan-title">${plan_title} Sponsorship</div>
				<div class="backing-plan-backers">${remaining}, ${ctx.format_currency(ctx.PLAN_AMOUNTS[plan])}/month</div>
				<div class="backing-plan-desc content">${ctx.PLAN_DESCRIPTIONS[plan]}</div>
				<div class="backing-plan-select${plan != 'platinum' and ' campaign-box-divider' or ''}${(not slots_available) and ' backing-plan-disabled' or ''}"><a href="/sponsor.gitfund?plan=${plan}">
				% if slots_available:
					Become a ${plan_title} Sponsor
				% else:
					All slots taken
				% endif
				</a></div>
			% endfor
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
