# -*- coding: utf-8 -*-
# Downloaded from https://github.com/sramana/pyatom at d1c03cfe1d47952625f98cd0d6f5fb349e09c2de
"""
    This module provides a class called :class:`AtomFeed` which can be
    used to generate feeds in the Atom syndication format (see :rfc:`4287`).

    Example::

        from pyatom import AtomFeed
        import datetime

        feed = AtomFeed(title="My Blog",
                        subtitle="My example blog for a feed test.",
                        feed_url="http://example.org/feed",
                        url="http://example.org",
                        author="Me")

        # Do this for each feed entry
        feed.add(title="My Post",
                 content="Body of my post",
                 content_type="html",
                 author="Me",
                 url="http://example.org/entry1",
                 updated=datetime.datetime.utcnow())

        print feed.to_string()

    :copyright: (c) 2010 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from datetime import datetime

XHTML_NAMESPACE = 'http://www.w3.org/1999/xhtml'


def escape(s, quote=False):
    """Replace special characters "&", "<" and ">" to HTML-safe sequences.  If
    the optional flag `quote` is `True`, the quotation mark character (") is
    also translated.

    There is a special handling for `None` which escapes to an empty string.

    :param s: the string to escape.
    :param quote: set to true to also escape double quotes.
    """
    if s is None:
        return ''
    elif hasattr(s, '__html__'):
        return s.__html__()
    elif not isinstance(s, basestring):
        s = unicode(s)
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    if quote:
        s = s.replace('"', "&quot;")
    return s


def _make_text_block(name, content, content_type=None):
    """Helper function for the builder that creates an XML text block."""
    if content_type == 'xhtml':
        return u'<%s type="xhtml"><div xmlns="%s">%s</div></%s>\n' % \
               (name, XHTML_NAMESPACE, content, name)
    if not content_type:
        return u'<%s>%s</%s>\n' % (name, escape(content), name)
    return u'<%s type="%s">%s</%s>\n' % (name, content_type,
                                         escape(content), name)


def format_iso8601(obj, timezone):
    """Format a datetime object for iso8601"""
    updated = '%Y-%m-%dT%H:%M:%S' + timezone
    return obj.strftime(updated)


class AtomFeed(object):
    """A helper class that creates Atom feeds.

    :param title: the title of the feed. Required.
    :param title_type: the type attribute for the title element.  One of
                       ``'html'``, ``'text'`` or ``'xhtml'``.
    :param url: the url for the feed (not the url *of* the feed)
    :param id: a globally unique id for the feed.  Must be an URI.  If
               not present the `feed_url` is used, but one of both is
               required.
    :param updated: the time the feed was modified the last time.  Must
                    be a :class:`datetime.datetime` object.  If not
                    present the latest entry's `updated` is used.
    :param timezone: the timezone is based on utc. format the "+0900"
    :param feed_url: the URL to the feed.  Should be the URL that was
                     requested.
    :param author: the author of the feed.  Must be either a string (the
                   name) or a dict with name (required) and uri or
                   email (both optional).  Can be a list of (may be
                   mixed, too) strings and dicts, too, if there are
                   multiple authors. Required if not every entry has an
                   author element.
    :param icon: an icon for the feed.
    :param logo: a logo for the feed.
    :param rights: copyright information for the feed.
    :param rights_type: the type attribute for the rights element.  One of
                        ``'html'``, ``'text'`` or ``'xhtml'``.  Default is
                        ``'text'``.
    :param subtitle: a short description of the feed.
    :param subtitle_type: the type attribute for the subtitle element.
                          One of ``'text'``, ``'html'``, ``'text'``
                          or ``'xhtml'``.  Default is ``'text'``.
    :param links: additional links.  Must be a list of dictionaries with
                  href (required) and rel, type, hreflang, title, length
                  (all optional)
    :param generator: the software that generated this feed.  This must be
                      a tuple in the form ``(name, url, version)``.  If
                      you don't want to specify one of them, set the item
                      to `None`.
    :param entries: a list with the entries for the feed. Entries can also
                    be added later with :meth:`add`.

    For more information on the elements see
    http://www.atomenabled.org/developers/syndication/

    Everywhere where a list is demanded, any iterable can be used.
    """

    default_generator = ('PyAtom', None, None)

    def __init__(self, title=None, entries=None, **kwargs):
        self.title = title
        self.title_type = kwargs.get('title_type', 'text')
        self.url = kwargs.get('url')
        self.feed_url = kwargs.get('feed_url', self.url)
        self.id = kwargs.get('id', self.feed_url)
        self.updated = kwargs.get('updated')
        self.timezone = kwargs.get('timezone', 'Z')
        self.author = kwargs.get('author', ())
        self.icon = kwargs.get('icon')
        self.logo = kwargs.get('logo')
        self.rights = kwargs.get('rights')
        self.rights_type = kwargs.get('rights_type')
        self.subtitle = kwargs.get('subtitle')
        self.subtitle_type = kwargs.get('subtitle_type', 'text')
        self.generator = kwargs.get('generator')
        if self.generator is None:
            self.generator = self.default_generator
        self.links = kwargs.get('links', [])
        self.entries = entries and list(entries) or []

        if not hasattr(self.author, '__iter__') \
           or isinstance(self.author, (basestring, dict)):
            self.author = [self.author]
        for i, author in enumerate(self.author):
            if not isinstance(author, dict):
                self.author[i] = {'name': author}

        if not self.title:
            raise ValueError('title is required')
        if not self.id:
            raise ValueError('id is required')
        for author in self.author:
            if 'name' not in author:
                raise TypeError('author must contain at least a name')

    def add(self, *args, **kwargs):
        """Add a new entry to the feed.  This function can either be called
        with a :class:`FeedEntry` or some keyword and positional arguments
        that are forwarded to the :class:`FeedEntry` constructor.
        """
        if len(args) == 1 and not kwargs and isinstance(args[0], FeedEntry):
            self.entries.append(args[0])
        else:
            kwargs['feed_url'] = self.feed_url
            kwargs['timezone'] = self.timezone
            self.entries.append(FeedEntry(*args, **kwargs))

    def __repr__(self):
        return '<%s %r (%d entries)>' % (
            self.__class__.__name__,
            self.title,
            len(self.entries)
        )

    def generate(self):
        """Return a generator that yields pieces of XML."""
        # atom demands either an author element in every entry or a global one
        if not self.author:
            if False in map(lambda e: bool(e.author), self.entries):
                self.author = ({'name': u'unbekannter Autor'},)

        if not self.updated:
            dates = sorted([entry.updated for entry in self.entries])
            self.updated = dates and dates[-1] or datetime.utcnow()

        yield u'<?xml version="1.0" encoding="utf-8"?>\n'
        yield u'<feed xmlns="http://www.w3.org/2005/Atom">\n'
        yield '  ' + _make_text_block('title', self.title, self.title_type)
        yield u'  <id>%s</id>\n' % escape(self.id)
        yield u'  <updated>%s</updated>\n' % format_iso8601(self.updated, self.timezone)
        if self.url:
            yield u'  <link href="%s" />\n' % escape(self.url, True)
        if self.feed_url:
            yield u'  <link href="%s" rel="self" />\n' % \
                escape(self.feed_url, True)
        for link in self.links:
            yield u'  <link %s/>\n' % ''.join('%s="%s" ' % \
                (k, escape(link[k], True)) for k in link)
        for author in self.author:
            yield u'  <author>\n'
            yield u'    <name>%s</name>\n' % escape(author['name'])
            if 'uri' in author:
                yield u'    <uri>%s</uri>\n' % escape(author['uri'])
            if 'email' in author:
                yield '    <email>%s</email>\n' % escape(author['email'])
            yield '  </author>\n'
        if self.subtitle:
            yield '  ' + _make_text_block('subtitle', self.subtitle,
                                          self.subtitle_type)
        if self.icon:
            yield u'  <icon>%s</icon>\n' % escape(self.icon)
        if self.logo:
            yield u'  <logo>%s</logo>\n' % escape(self.logo)
        if self.rights:
            yield '  ' + _make_text_block('rights', self.rights,
                                          self.rights_type)
        generator_name, generator_url, generator_version = self.generator
        if generator_name or generator_url or generator_version:
            tmp = [u'  <generator']
            if generator_url:
                tmp.append(u' uri="%s"' % escape(generator_url, True))
            if generator_version:
                tmp.append(u' version="%s"' % escape(generator_version, True))
            tmp.append(u'>%s</generator>\n' % escape(generator_name))
            yield u''.join(tmp)
        for entry in self.entries:
            for line in entry.generate():
                yield u'  ' + line
        yield u'</feed>\n'

    def to_string(self):
        """Convert the feed into a string."""
        return u''.join(self.generate())

    def __unicode__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string().encode('utf-8')


class FeedEntry(object):
    """Represents a single entry in a feed.

    :param title: the title of the entry. Required.
    :param title_type: the type attribute for the title element.  One of
                       ``'html'``, ``'text'`` or ``'xhtml'``.
    :param content: the content of the entry. Can either be a string or
                    a dictionary (or any class which inherits from 'dict').
                    If a dictionary is given, every key & value will serve
                    as attribute name & value, except for the 'content',
                    which can be used to embed content between the two
                    <content> tags.
    :param content_type: the type attribute for the content element.  One
                         of ``'html'``, ``'text'`` or ``'xhtml'``.
    :param summary: a summary of the entry's content.
    :param summary_type: the type attribute for the summary element.  One
                         of ``'html'``, ``'text'`` or ``'xhtml'``.
    :param url: the url for the entry.
    :param id: a globally unique id for the entry.  Must be an URI.  If
               not present the URL is used, but one of both is required.
    :param updated: the time the entry was modified the last time.  Must
                    be a :class:`datetime.datetime` object. Required.
    :param timezone: the timezone is based on utc. format the "+0900"
    :param author: the author of the feed.  Must be either a string (the
                   name) or a dict with name (required) and uri or
                   email (both optional).  Can be a list of (may be
                   mixed, too) strings and dicts, too, if there are
                   multiple authors. Required if not every entry has an
                   author element.
    :param published: the time the entry was initially published.  Must
                      be a :class:`datetime.datetime` object.
    :param rights: copyright information for the entry.
    :param rights_type: the type attribute for the rights element.  One of
                        ``'html'``, ``'text'`` or ``'xhtml'``.  Default is
                        ``'text'``.
    :param links: additional links.  Must be a list of dictionaries with
                  href (required) and rel, type, hreflang, title, length
                  (all optional)
    :param xml_base: The xml base (url) for this feed item.  If not provided
                     it will default to the item url.

    For more information on the elements see
    http://www.atomenabled.org/developers/syndication/

    Everywhere where a list is demanded, any iterable can be used.
    """

    def __init__(self, title=None, content=None, feed_url=None, **kwargs):
        self.title = title
        self.title_type = kwargs.get('title_type', 'text')
        self.content = content
        self.content_type = kwargs.get('content_type', 'html')
        self.url = kwargs.get('url')
        self.id = kwargs.get('id', self.url)
        self.updated = kwargs.get('updated')
        self.timezone = kwargs.get('timezone', 'Z')
        self.summary = kwargs.get('summary')
        self.summary_type = kwargs.get('summary_type', 'html')
        self.author = kwargs.get('author')
        self.published = kwargs.get('published')
        self.rights = kwargs.get('rights')
        self.links = kwargs.get('links', [])
        self.xml_base = kwargs.get('xml_base', feed_url)

        if not hasattr(self.author, '__iter__') \
           or isinstance(self.author, (basestring, dict)):
            self.author = [self.author]
        for i, author in enumerate(self.author):
            if not isinstance(author, dict):
                self.author[i] = {'name': author}

        if not self.title:
            raise ValueError('title is required')
        if not self.id:
            raise ValueError('id is required')
        if not self.updated:
            raise ValueError('updated is required')

    def __repr__(self):
        return '<%s %r>' % (
            self.__class__.__name__,
            self.title
        )

    def generate(self):
        """Yields pieces of ATOM XML."""
        base = ''
        if self.xml_base:
            base = ' xml:base="%s"' % escape(self.xml_base, True)
        yield u'<entry%s>\n' % base
        yield u'  ' + _make_text_block('title', self.title, self.title_type)
        yield u'  <id>%s</id>\n' % escape(self.id)
        yield u'  <updated>%s</updated>\n' % format_iso8601(self.updated, self.timezone)
        if self.published:
            yield u'  <published>%s</published>\n' % \
                  format_iso8601(self.published, self.timezone)
        if self.url:
            yield u'  <link href="%s" />\n' % escape(self.url)
        for author in self.author:
            yield u'  <author>\n'
            yield u'    <name>%s</name>\n' % escape(author['name'])
            if 'uri' in author:
                yield u'    <uri>%s</uri>\n' % escape(author['uri'])
            if 'email' in author:
                yield u'    <email>%s</email>\n' % escape(author['email'])
            yield u'  </author>\n'
        for link in self.links:
            yield u'  <link %s/>\n' % ''.join('%s="%s" ' % \
                (k, escape(link[k], True)) for k in link)
        if self.summary:
            yield u'  ' + _make_text_block('summary', self.summary,
                                           self.summary_type)
        if self.content:
            if issubclass(self.content.__class__, dict):
                if "content" in self.content:
                    yield u'  <content %s>%s</content>\n' % (' '.join('%s="%s"' % \
                        (k, escape(self.content[k], True)) for k in self.content if k != "content"), escape(self.content["content"]))
                else:
                    yield u'  <content %s/>\n' % ' '.join('%s="%s" ' % \
                        (k, escape(self.content[k], True)) for k in self.content)
            else:
                yield u'  ' + _make_text_block('content', self.content,
                                           self.content_type)
        yield u'</entry>\n'

    def to_string(self):
        """Convert the feed item into a unicode object."""
        return u''.join(self.generate())

    def __unicode__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string().encode('utf-8')
