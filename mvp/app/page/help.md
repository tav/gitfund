Please see below for answers to various frequently asked questions. If your
enquiry isn't answered by any of them, then please reach out to us directly via
team@gitfund.io.

FAQ:

[TOC]

### How do I update my sponsorship details?

You can update your details via the [manage sponsorship page](/manage.sponsorship).

### Are my contributions tax-deductible?

You should check with a tax professional in your country to be sure, but for
most countries, the amount you contribute as part of your sponsorship will not
be tax-deductible.

### Why are you only charging in GBP?

We've gone with just GBP for now as it is less work to support just a single
currency. Once the Beta is ready, we will add support for multiple currencies so
that most sponsors will be able to pay in their local currency.

### Why do you require VAT ID for EU sponsors?

As a VAT registered company in the UK and the rest of the EU, we need to charge
VAT. Unfortunately supporting VAT is not as simple as just adding a percentage
to the amount charged and introduces a lot of complexity, e.g.

* Having to account for currency exchange rates when the charged currency
  differs from the national currency of the relevant territory.

* Handling multiple rates within the same country.

* Edge cases when rates change.

* Producing and storing invoices appropriately.

* Validating and storing proof that a user is from a specific country.

So, for this MVP, we are only supporting business to business VAT, where the VAT
is reverse charged and much simpler to handle. And thus why we can only have EU
sponsors with a valid VAT ID at the moment.

Once the Beta is ready, this limitation will no longer apply as we will have
full VAT support — including for countries outside the EU.

### How do I get invoices?

We will only be adding support for auto-generated invoices (including VAT
invoices and credit notes) as part of our Beta. If you need invoices before
then, please email team@gitfund.io and we will manually generate them for you.

### Why is my sponsor image showing my personal profile picture?

We use the [Gravatar](https://en.gravatar.com/) service in order to
automatically find profile pictures based on email addresses. A lot of people
already have a Gravatar profile as it is used by popular services like
WordPress.

You can override the default by uploading the appropriate sponsor image via the
[update sponsor profile](/update.sponsor.profile) page.

### What happens if you don't raise your target?

Hopefully there will be enough interest in supporting the open source ecosystem
for us to raise our target.

But if by the end of September 2017 we still haven't reached it, then, depending
on the amount raised and our costs (especially with regards to legals and
compliance), we will either:

* Continue with the project — albeit delivering at a slightly slower pace than
  expected.

* Put the project on hold and cancel any further payments from sponsors. And
  will, of course, leave all of the GitFund code we'd developed till then as
  open source.

### How do I change the email address for my account?

Sorry, we haven't yet implemented support for changing the email address
associated with your account. We will do so as part of our core dev period
though.

### How do I change my password?

We use a passwordless system to authenticate users on the site. When you want to
sign in, we'll send you an email that contains a special authorised link.

### Are there any countries you definitely won't be supporting?

Given that open source is a global phenomena, we'll try as much as possible to
eventually support every country out there. If we don't support a country, then
it will be primarily due to one of three reasons:

* It's not supported by third-party payment processing services that we depend
  on.

* It's on an economic sanctions list of some kind.

* It has data protection requirements which require all personal data to be
  stored and processed within that territory and we are not able to figure out
  an easy, affordable, and reliable way of doing so for some reason.

### How do I cancel my sponsorship?

You can do so via the [cancel sponsorship page](/cancel.sponsorship).

### Why are displayed details not up-to-date?

In order to make the site load faster, we make extensive use of caching. This
sometimes results in stale information being shown for some time until the
caches get updated.
