### TL;DR

* We are building a new crowdfunding platform with a unique model as a solution to the [problem of funding in open source projects][ford-report].

* GitFund will make it easy for companies, who tend to be the biggest beneficiaries of open source, to support the projects that they depend on.

* Unlike most crowdfunding sites, who tend to take a 5% cut, we will be charging 0% platform fee so that projects will get as much of the money as possible.

* As an open source project ourselves, we're using the GitFund model to cover the costs of building and running GitFund.

* Help make GitFund happen by chipping in as an [individual donor](/back.gitfund)VAR-AVAILABLE-SLOT

* Help spread the word by sharing/upvoting this. Thanks!

### Why GitFund?

Open source is everywhere. From healthcare to education, scrappy startups to billion dollar giants, much of the software that runs our society is built using open source tools.

But despite playing such a vital role, many open source projects, and even the [supporting infrastructure][underfunded-infrastructure], are terribly under-resourced. And things have only gotten worse in recent years, e.g.

* As software eats the world, and the use of open source increases with it, it places ever increasing demands on the time of project maintainers.

* As more developers start settling down and having families, there are greater demands on their time. This leaves precious little free time for the [hard work][being-a-maintainer] of being an open source maintainer.

* Despite more people using open source today, there are proportionately fewer people contributing back. Everyone assumes that someone else is doing it.

It shouldn't take a crisis for us to pay attention, like we've had to do with [OpenSSL][openssl], [NTP][ntp], [GnuPG][gnupg], [RubyGems][rubygems], &c. Our software systems are becoming way too critical for that.

We desperately need a sustainable solution to the problem of [funding][ford-report] [open][isaacs] [source][nayafia]. And thus GitFund.

### The GitFund Model

GitFund is loosely based on the well-established event sponsorship model, i.e. Gold, Silver, Bronze sponsors, &c.

Each project, depending on its scale, defines the number of sponsorship tiers, the number of sponsorship slots per tier, and the amount that a sponsor has to contribute every month to secure that slot, e.g.

| Sponsorship Tier | Number of Sponsors | Monthly Amount          |
| :--------------- | :----------------- | :---------------------- |
| Gold             | 3                  | VAR-EXAMPLE-GOLD-SLOT   |
| Silver           | 10                 | VAR-EXAMPLE-SILVER-SLOT |
| Bronze           | 50                 | VAR-EXAMPLE-BRONZE-SLOT |

In addition to the sponsors, projects also define an unlimited Individual Donor tier for those who are happy to support the project in exchange for just having their name listed as a donor.

Some of the key aspects that set GitFund apart from the likes of [Kickstarter][kickstarter] and [Indiegogo][indiegogo] are:

* **Exclusively for Open Source**

  GitFund is being built specifically for the open source community, e.g. deep integration with GitHub, syntax highlighting within Markdown, [embedding asciicasts][asciicasts], integration with IRC/Slack, &c.

* **0% Platform Fee**

  Unlike most crowdfunding platforms, which tend to charge a 5% platform fee on top of payment processing fees, GitFund will not be charging a platform fee on the transactions made on the platform.

* **Distributed Payouts**

  The typical crowdfunding site expects projects to manually disburse the funds to individual collaborators. Given the distributed nature of open source, this is a lot of effort for most projects.

  In contrast, GitFund will enable maintainers to transfer funds from the project to individual collaborators — who can then have it paid out straight into their bank account — all directly from the platform.

  The received funds and transfers will also be viewable to all of the team members on a project — ensuring transparency and accountability within projects.

* **Targets Organizations**

  GitFund will provide organizations with [tangible benefits][benefits] so as to incentivize them to become sponsors. And, by making the whole process fairly streamlined, GitFund will reduce the barrier that currently exists in funding open source projects.

* **Multi-Currency Support**

  Open source is a global endeavour. Both sponsors and project developers are likely to come from anywhere in the world. GitFund will support as much of this global community as possible by adding support for multiple currencies, international bank accounts for withdrawals, &c.

* **Recurring Funding**

  Very few open source projects are ever "done". Technology is ever changing, and projects have to keep up with the times. In recognition of this, GitFund uses a monthly recurring model like Patreon so that projects can depend on a somewhat stable source of funding.

### Benefits to Sponsors

GitFund sets out to provide tangible benefits to project sponsors so as to make it easy for individuals to convince their organizations on the value of sponsoring specific projects:

* **Brand Visibility**

  By raising funds through GitFund, each project will be committing to embed a "Sponsored By" widget on their project README file and on the project documentation site (if one exists) — giving visibility to their sponsors.

  This widget will display, at random, a sponsor for each of the project's sponsorship tiers. On the README, this will show the sponsor's name and logo/profile image. On the website, it will also link to the sponsor's website.

* **Recruitment Ads**

  Sponsors will be able to use their displayed text/link on the "Sponsored By" widget to not just point to their site, but also for placing job ads, e.g. "We're looking for a Web Performance Engineers. Apply here!".

  What better place to recruit developers than on the documentation pages of the open source projects used by the company?

* **Sponsors-Only Issue Tracker**

  While sponsors won't have any control over the projects they are funding, they will have access to a Sponsors-only issue tracker on GitFund with support for upvoting issues — thus gently nudging the maintainers on what they consider to be important.

* **Sponsor Page**

  In the same way that companies like Microsoft gain kudos by having hundreds of projects and thousands of members on their [GitHub org page][microsoft-github-org], organizations will be able to show off their sponsorship of the open source ecosystem through a dedicated Sponsor Page.

* **Exclusivity**

  Unlike the standard donations-based model, where anyone can give and have their name attached to a project, the GitFund model provides sponsors with relative exclusivity due to the limited number of sponsorship slots.

And, of course, sponsors will benefit from the open source project itself! As long as a project is fully funded on GitFund, then sponsors should be able to be reasonably confident that it will stay healthy and actively maintained.

### Sponsor GitFund!

We are using this basic version of GitFund to raise sponsorship to cover the costs of developing and running GitFund itself. As a sponsor, you will get the full list of benefits listed above when the site goes live.

And thanks to the "Sponsored By" widget included in the site's footer, your sponsorship will be displayed across the whole of GitFund  — showing off just how awesome you are for making this [much needed infrastructure][ford-report] possible!

### Join the Community!

If you are excited by GitFund, then please do join one of the two community channels. For those who prefer IRC, there's #esp on chat.freenode.net:

* [chat.freenode.net/esp](irc://chat.freenode.net/esp)

And for those who prefer Slack, you can join via:

* [gitfund.io/community](https://gitfund.io/community)

Both channels are connected by a [relay bot][relay bot], so you won't be missing out on any discussions by choosing one over the other.

### Timeline/Budget

The initial Beta of GitFund will be ready for use by projects within 4-5 months of us hitting our monthly target of VAR-TARGET-SLOT.

This period will be used to set up the various legal requirements as well as to develop the site itself, with the setup/operating budget going towards:

<div class="image"><a href="/static/gfx/b9ff596df9a42b50a52653153816c6a56eb06328-budget-piechart.png"><img src="/static/gfx/b9ff596df9a42b50a52653153816c6a56eb06328-budget-piechart.png"></a></div>

The Beta will launch with an initial set of projects. If you'd like your project to be part of the Beta launch, then please [add your project here](/get.funded), and we'll get in touch before the launch.

And, if you can, chip in as an [individual donor](/back.gitfund) or get your company to [sponsor GitFund](/back.gitfund?plan=bronze). You will get lots of good karma and all of us in the open source community will be grateful for what you've made possible.

— Thank you, tav

### FAQ

#### Who are you?

We are the [Espians][espians], a small "remote-first" tech collective headquartered in London. We have been active members of the open source community since 1999 — starting with projects like Freenet, Jabber, LiteStep, Zope, &c.

We will initially be using Espians LLP, our existing legal entity, to operate GitFund. But once GitFund has been successfully running for a few years, we will look to separating it out into an independent non-profit.

#### What will happen if you don't raise your target?

Hopefully there will be enough interest in supporting the open source ecosystem for us to raise our target.

But if by the end of the year we still haven't reached it, then, depending on the amount raised and our costs (especially with regards to legals and compliance), we will either:

* Continue with the project — albeit delivering it at a slightly slower pace than expected.

* Put the project on hold and cancel any further payments from our supporters. In which case, we will of course leave all of the GitFund code we'd developed till then as open source.

#### How will the 0% platform fee work?

Unlike most crowdfunding sites, we will not be charging a platform fee on GitFund. This is possible due to a number of reasons:

* Since GitFund is not a venture-funded startup, we do not have to make a profit in order to keep investors happy.

* We will hold back 5% that will be used as a reserve to cover:

  * Any chargebacks across the whole platform, where we are not able to immediately recover the funds from the project where the chargeback occurred, i.e. due to funds already being paid out.

  * Any excess hosting/SaaS costs above our allocated budget of $3k/month.

  After 90 days, all unused amounts from the reserve will then be given back to the projects, in proportion to how much was taken from them.

  By structuring it this way, we can ensure that as much of the money reaches the intended developers, while still minimising our exposure to the risk of high growth/chargebacks.

Please note that while we won't be charging a platform fee, third-party payment processing fees will still apply, i.e. Stripe fees, bank transfer fees, &c.

#### Which code hosting services will you support?

We will be starting out with support for [GitHub] — including using it as our default namespace — as this is where the vast majority of open source projects are currently hosted.

Over time, if there's enough interest and we have enough resources, we'll also add support for other code hosting services like [Bitbucket] and [GitLab].

#### How do I get my project onto GitFund?

If you'd like your project to be part of the Beta launch, then please [add your project here](/get.funded), and we'll get in touch before the launch.

After the launch, anyone will be able to put their open source project onto GitFund, by just signing up and setting up the project. The only limitation will be for project members to live in one of our supported countries.

#### Which countries will you support?

Given that open source is a global phenomena, we'll try to eventually support every country out there. Backers, i.e. sponsors and donors, will be supported from most countries from the very start.

But due to regulatory/compliance and technical reasons, we won't be able to support withdrawals from all countries from the very start. This will be initially limited to those living in:

* Austria
* Belgium
* Denmark
* Finland
* France
* Germany
* Ireland
* Luxembourg
* Netherlands
* Norway
* Spain
* Sweden
* Switzerland
* United Kingdom
* United States

We will then gradually roll out support for the rest of the world — prioritizing [top Stack Overflow traffic sources][so-traffic], e.g. India, China, Brazil, Canada, Russia, Australia, &c.

If we don't support a country, then it will be primarily due to one of three reasons:

* It's not supported by any of the third-party payment processing services that we depend on, e.g. Stripe.

* It's on an economic sanctions list of some kind.

* It has data protection requirements which require all personal data to be stored and processed within that territory and we have not yet been able to figure out an affordable and reliable way of doing so.

#### How will the collection and distribution of funds work?

The original idea behind GitFund was to use [Stripe Connect][stripe-connect] to collect funds directly into each project's standalone Stripe account. But, from speaking to various projects, this wasn't ideal for a number of reasons:

* Each project would have to take on the burden of handling various taxes, e.g. the EU wants you to [charge/account for VAT][eu-vat] even if you only get 50 cents from a single sponsor in the EU.

* Each project would have to manually handle paying out the funds to the various developers. Not all developers were comfortable with sharing their bank details with project maintainers.

So, instead, the funds will be collected and distributed by GitFund directly as a sort of "sponsorship network" — similar to how [Google AdSense][adsense] collects money from advertisers and distributes it to publishers.

To elaborate:

1. Money from backers will be collected by GitFund using payment services like Stripe.

2. The collected money will then be credited to that project's fund on GitFund's internal system.

3. Project maintainers can then approve transfers from the project's fund to themselves and/or others on the project team using GitFund's internal system.

4. Money can then be withdrawn from the internal account it was transferred to, using one of the supported methods, e.g. bank transfer, payout to debit card, &c.

GitFund will handle the various regulatory requirements and taxes like VAT, so that developers will only have to account for the single UK-based income (where GitFund's legal entity is based) and any tax that may apply on that income.

#### How do you differ from OpenCollective?

Of the [hundreds of][hundreds of] [crowdfunding platforms][crowdfunding platforms] out there, [OpenCollective] is perhaps the most similar to GitFund. We certainly share the same ethos. However, our models differ in a number of key ways:

* They charge a 5-10% fee in contrast to our 0%.

* They give backers/sponsors a lot of choice in determining how much to give projects. In contrast, we believe that our more streamlined, tier-based approach will result in projects receiving more money.

* Their model is based around member collectives and requires collectives to have a fiscal sponsor to handle the finance admin. We will have no such requirement.

* Their current process requires a lot of manual steps. The only manual step we will have is a pretty light check to ensure that a project being listed is actually open source.

* Their current model/implementation is pretty US-centric and doesn't deal with a lot of regulatory issues in other countries. In contrast, we will serve as much of the global open source community as possible — starting with 15+ countries.

#### What are your major cost centers?

Even with a super lean dev team, it will still require a decent chunk of cash to be able to pull off something like GitFund. In particular, this is due to things like:

* **Legals/Compliance**

  Handling money is highly regulated in most countries. For example, in the UK, it is a criminal offence to not comply with [financial sanctions][ofsi] and you need to have a designated money laundering reporting officer as part of the regulated AML controls.

  Just getting the legal advice is expensive. And that's before implementing the relevant controls. And then when you consider that there are over 200 territories, each with their own set of requirements, you start to appreciate why it takes companies like Stripe so long to expand to new countries.

* **Customer Support**

  When it comes to anything to do with money, people expect first-class customer support, and are not so forgiving about poor service. We will need to have a reasonably-sized team of [Happiness Heroes][buffer] to deliver a decent customer service experience.

* **High Bandwidth Costs**

  GitFund will incur higher bandwidth costs per project than the typical crowdfunding site due to having to serve sponsor logos/images as part of the "Sponsored By" widgets on project sites. All those tens of kilobytes per image will add up pretty quickly, and cloud bandwidth is really pricey.

* **Chargeback Buffer**

  In addition to the standard 5% holdback, we will need an additional buffer from GitFund's operational budget in order to cashflow chargebacks. This will be particularly important in the early days when there may not be enough cash from the 5% held back from projects.

And then, of course, there's everything else that needs to be covered, e.g. accounting, community, design, dev, fraud ops, hosting, insurance, project management, security, sysadmin, testing, &c.

#### What are your major risks and challenges?

Behaviour change takes time. GitHub noticeably changed how many of us collaborate in the open source community. But this didn't happen overnight. Similarly, it will take a while before GitFunding is established as a cultural norm.

The introduction of money will no doubt add to the politics within certain projects. But we can try to learn from [the][openbsd] [larger][freebsd] [projects][linux] who have already had to deal with this, and hopefully, over time, some best practices will emerge.

#### How will you handle fraud?

We will be putting in place a number of controls to combat the inevitable fraud attempts that come with handling money online, e.g.

* Doing manual reviews of projects before they are published to ensure that they are legit open source projects.

* Using the social profiles of the project, sponsors, and team members to help determine the period that money is held (between 30-90 days) before it is paid out.

* Providing 2FA and audit logs so as to make authentication more secure.

* Building on top of machine learning-based tools like [Stripe Radar][radar] to minimize and prevent credit card fraud, money laundering, &c.

Where possible, we will try to be as transparent as possible as to the reasons for any holding periods on funds so that project maintainers can know if they can do anything to reduce it.

#### Does your brand violate the Git trademark?

It is our understanding that the [Git trademark][git-tm] doesn't apply to us as we will be operating under a different [trademark class][tm-class]. But we'll need to speak to an IP lawyer to verify this.

We've been quite lucky so far, as GitFund works pretty well as a name, and we've been able to get a decent domain, as well as the relevant social media accounts on [Facebook](https://www.facebook.com/GitFund), [Twitter](https://twitter.com/gitfund), and [GitHub](https://github.com/GitFund).

But, given that the Git trademark was a consideration in the Gittip guys [changing their name][gittip-name-change] to Gratipay, we've also come up with a few alternatives in case it turns out that we are violating the Git trademark.

#### Why do you require VAT ID from EU sponsors?

As a VAT registered company in the UK and the rest of the EU, we need to charge VAT. Unfortunately supporting VAT is not as simple as just adding a percentage to the amount charged and introduces a lot of complexity, e.g.

* Having to account for currency exchange rates when the charged currency differs from the national currency of the relevant country.

* Handling multiple rates within the same country.

* Edge cases when rates change.

* Producing and storing invoices appropriately.

* Validating and storing proof that a user is from a specific country.

So, for this MVP, we are only supporting business to business VAT in EU countries, where the VAT is reverse charged and much simpler to handle. And thus we are only supporting EU sponsors with a valid VAT ID at the moment.

Once the Beta is ready, this limitation will no longer apply as we will have full VAT support — including for countries outside the EU.

#### Who is on your Advisory Board?

We're super excited to have [Erik Moeller][eloquence] as the first member of our Advisory Board. During his time as the Deputy Director, he oversaw some pretty large funding campaigns at Wikimedia Foundation, and we are looking forward to learning from his experience.

If you know other amazing individuals who we can similarly learn from, please leave a comment below and we'll reach out to them.

#### Is GitFund open source?

Yes, the code for GitFund is open source and is being developed in the open. You can star/fork the repo here:

* [github.com/tav/gitfund](https://github.com/tav/gitfund)

This [MVP][mvp] runs on Python App Engine. The actual version will run using a minimal services framework with most of the code written in Go, and Rust used for some things like [syntax highlighting][syntect].

While the app as a whole will not be of much use to anyone besides us and our users, a lot of the code should prove useful to others, e.g. integrating with Stripe Connect, tools for handling taxes, compliance, &c.

[adsense]: https://www.google.co.uk/adsense/start/how-it-works/
[asciicasts]: https://asciinema.org/
[being-a-maintainer]: https://nolanlawson.com/2017/03/05/what-it-feels-like-to-be-an-open-source-maintainer/
[Bitbucket]: https://bitbucket.org/
[buffer]: https://open.buffer.com/customer-support-buffer/
[benefits]: #benefits-to-sponsors
[chargebacks]: https://stripe.com/docs/disputes/faq
[crowdfunding platforms]: https://wiki.snowdrift.coop/market-research/other-crowdfunding
[eloquence]: https://en.wikipedia.org/wiki/Erik_M%C3%B6ller
[espians]: http://espians.com
[eu-vat]: http://ec.europa.eu/taxation_customs/business/vat/telecommunications-broadcasting-electronic-services_en
[ford-report]: https://www.fordfoundation.org/library/reports-and-studies/roads-and-bridges-the-unseen-labor-behind-our-digital-infrastructure/
[freebsd]: https://www.freebsdfoundation.org/donors/
[git-tm]: https://git-scm.com/trademark
[GitLab]: https://gitlab.com/
[GitHub]: https://github.com
[gittip-name-change]: https://gratipay.news/gratitude-gratipay-ef24ad5e41f9
[gnupg]: https://www.propublica.org/article/the-worlds-email-encryption-software-relies-on-one-guy-who-is-going-broke
[hundreds of]: http://inside.gratipay.com/appendices/see-also/
[indiegogo]: https://www.indiegogo.com/
[isaacs]: https://medium.com/open-source-life/money-and-open-source-d44a1953749c
[kickstarter]: https://www.kickstarter.com/
[linux]: https://www.linuxfoundation.org/members/corporate
[many large tech firms]: https://www.glassdoor.co.uk/Salaries/san-francisco-senior-software-engineer-salary-SRCH_IL.0,13_IM759_KO14,38.htm
[microsoft-github-org]: https://github.com/microsoft
[mvp]: https://github.com/tav/gitfund/tree/master/mvp
[nayafia]: https://medium.com/%40nayafia/how-i-stumbled-upon-the-internet-s-biggest-blind-spot-b9aa23618c58
[ntp]: http://www.informationweek.com/it-life/ntps-fate-hinges-on-father-time/d/d-id/1319432
[openbsd]: http://www.openbsdfoundation.org/campaign2016.html
[OpenCollective]: https://opencollective.com/
[openssl]: http://veridicalsystems.com/blog/of-money-responsibility-and-pride/
[ofsi]: https://www.gov.uk/government/organisations/office-of-financial-sanctions-implementation
[radar]: https://stripe.com/radar
[redis]: https://redis.io/topics/sponsors
[relay bot]: https://github.com/tav/gitfund/tree/master/cmd/irc-slack
[rubygems]: http://andre.arko.net/2016/09/26/a-year-of-ruby-together/
[so-traffic]: https://www.quantcast.com/stackoverflow.com#/geographicCard
[sponsor]: /sponsor.gitfund
[stripe-connect]: https://stripe.com/connect
[stripe-global]: https://stripe.com/global
[syntect]: https://github.com/trishume/syntect
[tm-class]: https://en.wikipedia.org/wiki/International_(Nice)_Classification_of_Goods_and_Services
[tragedy-of-the-commons]: https://en.wikipedia.org/wiki/Tragedy_of_the_commons
[underfunded-infrastructure]: https://talkpython.fm/episodes/show/84/are-we-failing-to-fund-python-s-core-infrastructure
