# These GitHub-Flavoured Markdown extensions are adapted from:
# https://github.com/google/py-gfm/tree/master/gfm

# Copyright 2012, the Dart project authors. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
#     * Neither the name of Google Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re

from markdown import Extension

from markdown.inlinepatterns import (
    BRK, IMAGE_LINK_RE, IMAGE_REFERENCE_RE, ImagePattern,
    ImageReferencePattern, LINK_RE, LinkPattern, NOIMG, Pattern,
    REFERENCE_RE, ReferencePattern, SimpleTagPattern
    )

from markdown.util import AtomicString
from markdown.util import etree

SPACE = r"(?:\s*(?:\r\n|\r|\n)?\s*)"
SPACED_LINK_RE = LINK_RE.replace(NOIMG + BRK, NOIMG + BRK + SPACE)
SPACED_REFERENCE_RE = REFERENCE_RE.replace(NOIMG + BRK, NOIMG + BRK + SPACE)
SPACED_IMAGE_LINK_RE = IMAGE_LINK_RE.replace(r'\!' + BRK, r'\!' + BRK + SPACE)
SPACED_IMAGE_REFERENCE_RE = IMAGE_REFERENCE_RE.replace(r'\!' + BRK, r'\!' + BRK + SPACE)
STRIKE_RE = r'(~{2})(.+?)(~{2})' # ~~strike~~

class AutolinkPattern(Pattern):
    def handleMatch(self, m):
        el = etree.Element("a")
        href = m.group(2)
        if not re.match('^(ftp|https?)://', href, flags=re.IGNORECASE):
            href = 'http://%s' % href
        el.set('href', self.unescape(href))
        el.text = AtomicString(m.group(2))
        return el

class AutolinkExtension(Extension):
    """
    An extension that turns all URLs into links.

    Note: GitHub only accepts URLs with protocols or "www.", whereas Gruber's
    regex accepts things like "foo.com/bar".
    """

    def extendMarkdown(self, md, md_globals):
        url_re = r'(?i)\b((?:(?:ftp|https?)://|www\d{0,3}[.])(?:[^\s()<>]+|' + \
            r'\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()' + \
            r'<>]+\)))*\)|[^\s`!()\[\]{};:' + r"'" + ur'".,<>?«»“”‘’]))'
        autolink = AutolinkPattern(url_re, md)
        md.inlinePatterns.add('gfm-autolink', autolink, '_end')

class AutomailPattern(Pattern):
    def handleMatch(self, m):
        el = etree.Element("a")
        el.set('href', self.unescape('mailto:' + m.group(2)))
        el.text = AtomicString(m.group(2))
        return el

class AutomailExtension(Extension):
    """An extension that turns all email addresses into links."""

    def extendMarkdown(self, md, md_globals):
        mail_re = r'\b(?i)([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]+)\b'
        automail = AutomailPattern(mail_re, md)
        md.inlinePatterns.add('gfm-automail', automail, '_end')

class SpacedLinkExtension(Extension):
    """
    An extension that supports links and images with additional whitespace.

    GitHub's Markdown engine allows links and images to have whitespace --
    including a single newline -- between the first set of brackets and the
    second (e.g. ``[text] (href)``). Python-Markdown does not, but this
    extension adds such support.
    """

    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns["link"] = LinkPattern(SPACED_LINK_RE, md)
        md.inlinePatterns["reference"] = ReferencePattern(SPACED_REFERENCE_RE, md)
        md.inlinePatterns["image_link"] = ImagePattern(SPACED_IMAGE_LINK_RE, md)
        md.inlinePatterns["image_reference"] = ImageReferencePattern(SPACED_IMAGE_REFERENCE_RE, md)

class StrikethroughExtension(Extension):
    """An extension that supports PHP-Markdown style strikethrough."""

    def extendMarkdown(self, md, md_globals):
        pattern = SimpleTagPattern(STRIKE_RE, 'del')
        md.inlinePatterns.add('gfm-strikethrough', pattern, '_end')

