### TL;DR

* We are building a sustainable solution to the [problem of funding open source projects][ford-report].

* GitFund will make it easy for companies, who tend to be biggest beneficiaries of open source, to give back to the projects that they depend on.

* Unlike most crowdfunding sites, who tend to take a 5% cut, we will be charging 0% platform fee so that projects will get as much of the money as possible.

* We'll also be pretty unique in supporting distributed payouts, so that all collaborators can be paid directly on the platform from project funds.

* Get your company [to sponsor GitFund](/sponsor.gitfund). We only need 75 sponsors to make this real! And, even at our highest tier, it's still less than the cost of a single senior dev at [many large tech firms].

### Why GitFund?

Open source is everywhere. From healthcare to education, scrappy startups to billion dollar giants, much of the software that runs our society is built using open source tools.

But despite playing such a vital role, many open source projects, and even [supporting infrastructure][underfunded-infrastructure], are terribly under-resourced. And things have only gotten worse in recent years, e.g.

* As software eats the world, and the use of open source increases with it, it places ever increasing demands on the time of project maintainers.

* As more developers start settling down and having families, there are greater demands on their time. This leaves precious little free time for the [hard work][being-a-maintainer] of being an open source maintainer.

* Despite more people using open source today, there are proportionately fewer people contributing back. Everyone assumes that someone else is doing it.

It shouldn't take a crisis for us to pay attention, like we've had to do with [OpenSSL][openssl], [NTP][ntp], [GnuPG][gnupg], [RubyGems][rubygems], &c. Our software systems are becoming way too critical for that.

We desperately need a sustainable solution to the problem of [funding][ford-report] [open][isaacs] [source][nayafia]. And thus GitFund.

### The GitFund Model

GitFund is loosely based on the well-established event sponsorship model, i.e. Gold, Silver, Bronze sponsors, &c.

Each project, depending on its scale, defines the number of sponsorship tiers, the number of sponsorship slots per tier, and the amount that a sponsor has to contribute every month to secure that slot, e.g.

| Sponsorship Tier | Number of Sponsors | Monthly Amount |
| :--------------- | :----------------- | :------------- |
| Gold             | 3                  | $3,000         |
| Silver           | 10                 | $600           |
| Bronze           | 100                | $30            |

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

  The majority of the crowdfunding systems used by open source projects tend to target individuals. And while the goodwill of altruistic individuals has kept our community alive, the main beneficiaries of open source tend to be organizations.

  GitFund will provide these organizations with [tangible benefits][benefits] so as to incentivize them to become sponsors. And, by making the whole process fairly streamlined, GitFund will reduce the barrier that currently exists in funding open source projects.

* **Multi-Currency Support**

  Open source is a global endeavour. Both sponsors and project developers are likely to come from anywhere in the world. GitFund will support as much of this global community as possible by adding support for multiple currencies, international bank accounts for withdrawals, &c.

* **Recurring Funding**

  Very few open source projects are ever "done". Technology is ever changing, and projects have to keep up with the times. In recognition of this, GitFund uses a monthly recurring model so that projects can depend on a somewhat stable source of funding.

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

* **Hassle Free**

  By streamlining the process of sponsoring projects, GitFund will dramatically simplify life for sponsors. No need to go through lengthy negotiations for each project you want to sponsor. No need to figure out tax deducations. Cancel whenever you want. &c.

And, of course, sponsors will benefit from the open source project itself! As long as a project is fully funded on GitFund, then sponsors should be able to be reasonably confident that it will stay healthy and actively maintained.

### Sponsor GitFund!

We are using this basic version of GitFund to raise sponsorship to cover the costs of developing and running GitFund itself. As a sponsor, you will get the full list of benefits listed above when the site goes live.

And thanks to the "Sponsored By" widget included in the site's footer, your sponsorship will be displayed across the whole of GitFund  — showing off just how awesome you are for making this [much needed infrastructure][ford-report] possible!

### Timeline

The initial Beta of GitFund will be ready for use by projects within 4 months of us hitting our target. This period will be used to set up the various legal/regulatory requirements as well as to develop the site itself.

The Beta will launch with an initial set of projects. If you'd like your project to be part of the Beta launch, then please leave a supportive comment below with a brief description and a link to your project/repo.

### 0% Platform Fee

Unlike most crowdfunding sites, we will not be charging a platform fee on GitFund. This is possible due to a number of reasons:

* Since GitFund is not a venture-funded startup, we do not have to make a profit in order to keep investors happy.

* We will hold back 10% that will be used as a reserve to cover:

  * Any chargebacks across the whole platform, where we are not able to immediately recover the funds from the project where the chargeback occurred, i.e. due to funds already being paid out.

  * Any excess hosting costs above our allocated budget of £5k/month.

  After 90 days, all unused amounts from the reserve will then be given back to the projects, in proportion to how much was taken from them.

  By structuring it this way, we can ensure that as much of the money reaches the intended developers, while still minimising our exposure to the risk of high growth/chargebacks.

Please note that while we won't be charging a platform fee, third-party payment processing fees will still apply, i.e. Stripe fees, bank transfer fees, &c.

### Operational Costs

Even with a super lean dev team, it still requires a decent chunk of cash to be able to pull off something like GitFund. In particular, this is due to things like:

* **Legals/Compliance**

  Handling money is highly regulated in most countries. For example, in the UK, it is a criminal offence to not comply with [financial sanctions][ofsi] and you need to have a designated money laundering reporting officer as part of the regulated AML controls.

  Just getting the legal advice is expensive. And that's before implementing the relevant controls. And then when you consider that there are over 200 territories, each with their own set of requirements and license fees, you start to appreciate why it takes companies like Stripe so long to expand to new countries.

* **Customer Support**

  When it comes to anything to do with money, people expect first-class customer support, and are not so forgiving about poor service. We will need to have a reasonably-sized team of [Happiness Heroes][buffer] to deliver a decent customer service experience.

* **High Bandwidth Costs**

  GitFund will incur higher bandwidth costs per project than the typical crowdfunding site due to having to serve sponsor logos/images as part of the "Sponsored By" widgets on project sites. All those tens of kilobytes per image will add up pretty quickly, and cloud bandwidth is really pricey.

* **Chargeback Buffer**

  In addition to the standard 10% holdback, we will need an additional buffer from GitFund's operational budget in order to cashflow chargebacks. This will be particularly important in the early days when there may not be enough cash from the 10% held back from projects.

And then, of course, there's everything else that needs to be covered, e.g. accounting, community, design, dev, fraud ops, hosting, insurance, project management, security, sysadmin, testing, &c.

### Flow of Money

The original idea behind GitFund was to use [Stripe Connect][stripe-connect] to collect funds directly into each project's Stripe account. But, from speaking to various projects, this wasn't ideal for a number of reasons:

* Each project would have to take on the burden of handling various taxes, e.g. the EU wants you to [charge/account for VAT][eu-vat] even if you only get 50 cents from a single sponsor in the EU.

* Each project would have to manually handle paying out the funds to the various developers. Not all developers were comfortable with sharing their bank details with project maintainers.

So, instead, the funds will be collected and distributed by GitFund directly as a sort of "sponsorship network" — similar to how [Google AdSense][adsense] collects money from advertisers and distributes it to publishers.

To elaborate:

1. Money from sponsors will be collected by GitFund using Stripe.

2. Each project's sponsorship money will then be credited to that project's fund on GitFund's internal system.

3. Project maintainers can then approve transfers from the project's fund to themselves and/or others on the project team using GitFund's internal system.

4. Money can then be withdrawn from the internal account it was transferred to, using one of the supported methods, e.g. bank transfer, payout to debit card, &c.

GitFund will handle the various regulatory requirements and taxes like VAT, so that developers will only have to account for the single UK-based income (where GitFund's legal entity is based) and any tax that may apply on that income.

### Supported Territories

Due to both regulatory/compliance reasons and technical reasons like being able to do electronic bank transfers, we won't be able to support withdrawals from all territories from the very start.

We will initially start with support for [the countries supported by Stripe][stripe-global]. And then gradually roll out support for all other territories — prioritizing [top Stack Overflow traffic sources][so-traffic].

### Fraud Prevention

We will be putting in place a number of controls to combat the inevitable fraud attempts that come with handling money online, e.g.

* Doing manual reviews of projects before they are published to ensure that they are legit open source projects.

* Using the social profiles of the project, sponsors, and team members to help determine the period that money is held (between 30-90 days) before it is paid out.

* Providing 2FA and audit logs so as to make authentication more secure.

* Building on top of machine learning tools like [Stripe Radar][radar] to minimize and prevent credit card fraud, money laundering, &c.

Where possible, we will try to be as transparent as possible as to the reasons for any holding periods on funds so that project maintainers can know if they can do anything to reduce it.

### Risks and Challenges

Behaviour change takes time. GitHub noticeably changed how many of us collaborate in the open source community. But this didn't happen overnight. Similarly, it will take a while before GitFunding is established as a cultural norm.

The introduction of money will no doubt add to the politics within certain projects. But we can try to learn from [the][openbsd] [larger][freebsd] [projects][linux] who have already had to deal with this, and hopefully, over time, some best practices will emerge.

### Finalising the Brand

Coming up with a good name for a project is never easy. And although GitFund works well as name, it may potentially be in violation of the [Git trademark policy][git-tm], e.g. why the Gittip guys [changed their name][gittip-name-change] to Gratipay.

It is our understanding that the Git trademark doesn't apply to us as we will be operating under a different [trademark class][tm-class]. But we'll need to speak to an IP lawyer to verify this.

### GitFund is Open Source

The code for GitFund is open source and developed in the open. You can star/fork the repo here:

* [github.com/tav/gitfund](https://github.com/tav/gitfund)

This [MVP][mvp] runs on Python App Engine. The actual version will run using a minimal services framework with most of the code in Go, and Rust used for some things like [syntax highlighting][syntect].

While the app as a whole will not be of much use to anyone besides us and our users, a lot of the code should prove useful to others, e.g. integrations with platforms like Stripe Connect, tools for handling taxes, compliance, &c.

### About Us

We are the [Espians][espians], a small "remote-first" tech collective headquartered in London. We have been active members of the open source community since 1999 — starting with projects like Freenet, Jabber, LiteStep, Zope, &c.

We will initially be using Espians LLP, our existing legal entity, to operate GitFund. But once GitFund has been successfully running for a few years, we will separate it out into an independent non-profit.

### Advisory Board

We're super excited to have [Erik Moeller][eloquence] as the first member of our Advisory Board. During his time as the Deputy Director, he oversaw some pretty large funding campaigns at Wikimedia Foundation, and we are looking forward to learning from his experience.

If you know other amazing individuals who we can similarly learn from, please leave a comment below and we'll reach out to them.

### Join the Community!

If you are excited by GitFund, then please do join one of the two community channels. For those who prefer IRC, there's #esp on chat.freenode.net:

* [chat.freenode.net/esp](irc://chat.freenode.net/esp)

And for those who prefer Slack, you can join via:

* [gitfund.io/community](https://gitfund.io/community)

Both channels are connected by a [relay bot][relay bot], so you won't be missing out on any discussions by choosing one over the other.

### Call to Action

In closing, [please sponsor GitFund][sponsor] if you can, or get your company to sponsor GitFund. You will get lots of good karma and all of us in the open source community will be grateful for what you've made possible.

And do leave a comment if you like the idea of GitFund. It will be great to hear about any features you'd like to see, if you'd like to collaborate, or have your project be part of the Beta launch.

— Cheers, tav

[adsense]: https://www.google.co.uk/adsense/start/how-it-works/
[asciicasts]: https://asciinema.org/
[being-a-maintainer]: https://nolanlawson.com/2017/03/05/what-it-feels-like-to-be-an-open-source-maintainer/
[buffer]: https://open.buffer.com/customer-support-buffer/
[benefits]: #benefits-to-sponsors
[chargebacks]: https://stripe.com/docs/disputes/faq
[eloquence]: https://en.wikipedia.org/wiki/Erik_M%C3%B6ller
[espians]: http://espians.com
[eu-vat]: http://ec.europa.eu/taxation_customs/business/vat/telecommunications-broadcasting-electronic-services_en
[ford-report]: https://www.fordfoundation.org/library/reports-and-studies/roads-and-bridges-the-unseen-labor-behind-our-digital-infrastructure/
[freebsd]: https://www.freebsdfoundation.org/donors/
[git-tm]: https://git-scm.com/trademark
[gittip-name-change]: https://gratipay.news/gratitude-gratipay-ef24ad5e41f9
[gnupg]: https://www.propublica.org/article/the-worlds-email-encryption-software-relies-on-one-guy-who-is-going-broke
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
