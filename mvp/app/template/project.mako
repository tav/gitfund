<% prices = ctx.PRICES_INDEX[ctx.TERRITORY2PRICES[territory]] %>
<div class="campaign">
<div class="campaign-header">
	<div class="campaign-banner"><div class="inner">
		<div class="progress-bar">
			<div class="progress-bar-fill" style="width: ${totals.percent}%"></div>
		</div>
		<div class="info"><strong>${"{:,}".format(totals.backers)}</strong> ${ctx.pluralise('backer', totals.backers)}</div>
		<div class="info info-target"><strong class="price-info-target">${prices[ctx.PRICES_POS['target']]}</strong> / month target</div>
		<div class="info info-raised" style="display: none;">raised approx.&nbsp; <strong>$${totals.raised}</strong> per month</div>
		% if ctx.user and ctx.user.backer:
		<a class="sponsor" href="/manage.subscription">Manage Backing</a>
		% else:
		<a class="sponsor" href="/back.gitfund">Back This Project</a>
		% endif
	</div></div>
</div>
<div class="clear"></div>
<div class="campaign-cols"><div class="campaign-inner">
	% if thanks:
	<div class="alert-green">Your backing is being processed. Thank you for your support!</div>
	% endif
	% if ctx.preview_mode:
	<div class="preview-warn">This is for preview only. Please do not share publicly. Thank you.</div>
	% endif
	<div class="project-title inner-pad-only">${ctx.CAMPAIGN_TITLE|h}</div>
	<div class="project-image inner-pad-only"><a href="${ctx.STATIC('gfx/gitfund-overview.png')}"><img src="${ctx.STATIC('gfx/gitfund-overview.png')}" style="width: 100%"></a></div>
	<div class="inner-pad-only project-activity-bar">
		<a class="button-twitter" href="https://twitter.com/intent/tweet/?${ctx.urlencode({'text': 'Check out ' + ctx.site_title.encode('utf-8'), 'url': 'https://gitfund.io/tav/gitfund'})}"><span>Tweet</span></a>
		<a class="button-facebook" href="https://facebook.com/sharer/sharer.php?${ctx.urlencode({'u': 'https://gitfund.io/tav/gitfund'})}"><span>Share</span></a>
		<br>
		<a class="ghb" href="https://github.com/tav/gitfund"><span class="ghb-left"><span class="ghb-icon"></span><span class="ghb-repo">gitfund</span></span><span class="ghb-right"><span class="ghb-star"></span><span class="ghb-count">${social.repo.stars}</span></span></a>
		<a href="#disqus_thread" data-disqus-identifier="tav/gitfund" id="disqus_count" class="comment-link">Leave a comment</a>
	</div>
	<div id="campaign-content" class="campaign-col1 collapse-mobile">
		<div class="campaign-box content inner-pad-only">
			${ctx.render_campaign_content(territory, totals.sponsor_plans)}
		</div>
		<div class="read-full"><a href="" class="read-full-link">READ FULL ARTICLE</a></div>
	</div>
	<div class="campaign-col2">
		<div>
			<div class="campaign-box-inner price-switcher">
				<p>Switch currency:</p>
				<div class="select-box"><select id="price-updater">
				% for tset in ctx.TERRITORIES:
					% if len(tset) != 1:
					<optgroup label="${tset[-1][0]}">
					% endif
					% for territory_name, territory_code in tset:
					<option value="${territory_code}"${territory_code == territory and ' selected="selected"' or ''}>${territory_name}</option>
					% endfor
					% if len(tset) != 1:
					</optgroup>
					% endif
				% endfor
				</select></div>
			</div>
		</div>
		% if not (ctx.user and ctx.user.backer):
		<div class="campaign-box">
			<div class="campaign-box-inner">
			% for plan in ['donor', 'bronze', 'silver', 'gold', 'platinum']:
				<%
					plan_title = ctx.DETAILED_DEFAULT[ctx.PRICES_POS[plan + '-detailed']]
					if plan == 'donor':
						info = '%s %s so far' % (totals.donors, ctx.pluralise('donor', totals.donors))
						slots_available = True
					else:
						slots_total = ctx.PLAN_SLOTS[plan]
						slots_available = max(slots_total - totals.sponsor_plans[plan], 0)
						if not slots_available:
							info = 'All %s slots taken' % slots_total
						elif slots_available == slots_total:
							info = '%s slots available' % slots_available
						else:
							info = '%s of %s slots left' % (slots_available, slots_total)
				%>
				<div class="backing-plan-title">${plan_title}</div>
				<div class="backing-plan-backers">${info}, <span class="price-info-${plan}-plain">${prices[ctx.PRICES_POS[plan + '-plain']]}</span> / month</div>
				<div class="backing-plan-desc">${ctx.PLAN_DESCRIPTIONS[plan]}</div>
				<div class="backing-plan-select${(not slots_available) and ' backing-plan-disabled' or ''}"><a href="/back.gitfund?plan=${plan}">
				% if plan == 'donor':
					Become an Individual Donor
				% elif slots_available:
					Become a ${plan_title}
				% else:
					All slots taken
				% endif
				</a></div>
			% endfor
			</div>
		</div>
		% endif
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
				% elif profile.main == 'github':
				<div class="team-profile-image"><img src="${github.avatar}"></div>
				% endif
				<div class="team-profile-bio">${profile.role|h}</div>
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
			<div class="campaign-box-title">WANT TO HELP?</div>
			<div class="campaign-box-inner-sides">
				<div class="ambassador-button">
					<a href="/site/ambassadors">Become an Ambassador!</a>
				</div>
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
	<div class="campaign-col1">
		<div class="inner-pad-only"><div class="disqus">
			<div id="disqus_thread"></div>
		</div></div>
	</div>
</div></div>
<div class="clear"></div>
</div>
