We are strong believers in [FLO systems]. That is, Free/Libre/Open systems. Our
belief is publicly backed up by our actions — in that we release almost all of
our work into the [Public Domain].

There are, however, circumstances in which we cannot always stick to our ideals
and have to make some compromises — especially with regards to using certain
third-party proprietary systems.

By documenting the various compromises that we are making, we hope to:

1. Make both ourselves and the broader community more conscious of it so that we
   may be better placed to re-evaluate decisions as conditions change.

2. Acknowledge some of the valid concerns raised by those who are more principled
   than us, even as we make various compromises for pragmatic reasons.

### Our Compromises

Please note that our decision making is based purely on our opinion, and just
because we state our opinions to be a certain way doesn't mean that they have to
be true for anyone else:

* We use the term "open source" almost exclusively and in preference to "free
  software" or "FLO", as open source is well-recognized and doesn't have the
  confusion of the term "free".

* We use [Amazon Route 53] and [DNS Made Easy] to handle our DNS. At our small
  scale, this is more cost effective than running our own DNS servers —
  especially given considerations like DDoS.

* We use [G Suite] and [Mailjet] to handle our email. Again, at our scale, this
  is more cost effective than managing it ourselves — especially given
  considerations like spam and deliverability.

* We will be integrating very closely with [GitHub]. We recognize the criticisms
  made against GitHub in that it is proprietary and encourages an unnecessary
  dependency on a centralized resource, but:

  * The vast majority of projects are already on there. And it makes sense for
    us to be where the community is.

  * The social graph on GitHub provides us with a very useful dataset that will
    help us combat potential fraud by assessing the relative reputation of
    individuals.

  * We prefer how they handle namespaces, i.e. with repos hanging off of users
    and orgs. They've done a great job of curating this namespace — saving us
    the headache of having to do it.

* We are temporarily using [Google Analytics] for website analytics. But given
  both its proprietary nature and privacy implications, will be replacing it
  with an in-house, open solution within the coming months.

  * We recognize that due to the use of adblockers, we will be getting
    incomplete data from Google Analytics. But, since we are using [App Engine]
    for this MVP, it's still more practical to use it than to build some tooling
    around the App Engine logs.

* We will be using a number of proprietary services from Google Cloud.
  Specifically: [Compute Engine], [Cloud Load Balancer], [Cloud Storage], and
  [Cloud Spanner][Cloud Spanner]:

  * We recognize that this will create a certain amount of lock-in with Google
    Cloud, but given our limited resources and relatively small scale, this is
    more cost effective for us.

  * For example, even given the relatively high cost of Cloud Spanner, it will
    still cost us a lot less than it would to hire a single decent DBA to
    administer/manage/scale something like [PostgreSQL].

  * Similarly, we imagine our Cloud Storage costs will be a fraction of the
    amount it would cost to hire someone skilled enough in setting up and
    maintaining a production-ready [Ceph cluster].

  * However, as we grow, we will actively look into using (or perhaps even
    building) open source alternatives that provide us with similar
    functionality without any of the administrative burden.

* Many of our team members use proprietary operating systems like [macOS],
  [iOS], and [Windows]. While this is not ideal:

  * We have yet to find GNU/Linux laptops that meet our requirements in terms of
    aesthetics, build quality, driver support (especially for GPUs), and user
    experience.

  * We believe that iPhones tend to be more secure and provide a more consistent
    user experience than alternatives. However, we are hopeful that this might
    change with the advent of [Fuchsia].

* We use [Stripe] for handling financial transactions (from card payments to
  making payouts to bank accounts). This is far more cost effective and a lot
  less painful than doing it ourselves:

  * Given the huge amount of regulation around payment processing and the
    transfer of funds, it would take hundreds of man-years of work to even come
    close to what Stripe offers.

  * And even if we were successful in building an open source alternative, it
    would still depend on various proprietary systems and licenses for
    regulatory/compliance reasons.

  * While we recognize the objections that some people have against running
    [proprietary javascript], using [Stripe.js] on our site saves us having to
    deal with a lot of the burdens of PCI compliance.

  * As to building on top of platforms like [Ethereum], we don't believe any of
    them are suitable yet. And we say this as big believers in crypto-systems,
    e.g. many Espians worked on [Opencoin] before Bitcoin was even released.

    And even if a suitable platform were to emerge in the future, it would still
    require a lot of work to satisfy the various regulations and interface with
    the "legacy" financial institutions.

### Adapting to the Future

It is said that perfect is the enemy of good. And while having to make these
compromises is less than ideal, we hope that it will enable us to do more good
than harm.

And, of course, as conditions change, e.g. as viable open source alternatives
emerge to any of the proprietary systems we are using, we will re-evaluate our
position and decide appropriately.

*This document was inspired by a conversation with [Aaron Wolf], and was [last
updated][revisions] on 2017-06-06.*

[Aaron Wolf]: https://github.com/wolftune
[Amazon Route 53]: https://aws.amazon.com/route53/
[App Engine]: https://cloud.google.com/appengine/
[Ceph cluster]: http://docs.ceph.com/docs/master/start/quick-ceph-deploy/
[Cloud Load Balancer]: https://cloud.google.com/load-balancing/
[Cloud Spanner]: https://cloud.google.com/spanner/
[Cloud Storage]: https://cloud.google.com/storage/
[Compute Engine]: https://cloud.google.com/compute/
[DNS Made Easy]: https://www.dnsmadeeasy.com/
[Ethereum]: https://www.ethereum.org/
[FLO systems]: https://wiki.snowdrift.coop/about/free-libre-open
[Fuchsia]: https://en.wikipedia.org/wiki/Google_Fuchsia
[G Suite]: https://gsuite.google.com/
[GitHub]: https://github.com/
[Google Analytics]: https://analytics.google.com/
[iOS]: https://developer.apple.com/ios/
[macOS]: https://developer.apple.com/macos/
[Mailjet]: https://www.mailjet.com/
[misses-the-point]: https://www.gnu.org/philosophy/open-source-misses-the-point.html
[Opencoin]: https://opencoin.org/
[proprietary javascript]: https://www.gnu.org/philosophy/javascript-trap.html
[revisions]: https://github.com/tav/gitfund/commits/master/mvp/app/page/flos-statement.md
[PostgreSQL]: https://www.postgresql.org/
[Public Domain]: https://github.com/tav/gitfund/blob/master/UNLICENSE.md
[Stripe]: https://stripe.com/
[Stripe.js]: https://stripe.com/docs/stripe.js
[Windows]: https://www.microsoft.com/windows/
[won in terms of mindshare]: https://trends.google.com/trends/explore?date=all&q=%22free%20software%22,%22open%20source%22
