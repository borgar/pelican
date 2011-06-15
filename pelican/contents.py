# -*- coding: utf-8 -*-
from pelican.utils import slugify, truncate_html_words, format_url
from pelican.log import *
from pelican.settings import _DEFAULT_CONFIG
from os import getenv

class Page(object):
    """Represents a page
    Given a content, and metadata, create an adequate object.

    :param content: the string to parse, containing the original content.
    """
    mandatory_properties = ('title',)
    default_urls = ('pages/:title.html', 'pages/:title-:lang.html',)

    def __init__(self, content, metadata=None, settings=None, filename=None):
        # init parameters
        if not metadata:
            metadata = {}
        if not settings:
            settings = _DEFAULT_CONFIG

        self._content = content
        self.translations = []

        self.status = "published"  # default value

        local_metadata = dict(settings.get('DEFAULT_METADATA', ()))
        local_metadata.update(metadata)

        # set metadata as attributes
        for key, value in local_metadata.items():
            setattr(self, key.lower(), value)
        
        # default author to the one in settings if not defined
        if not hasattr(self, 'author'):
            if 'AUTHOR' in settings:
                self.author = settings['AUTHOR']
            else:
                self.author = getenv('USER', 'John Doe')
                warning("Author of `{0}' unknow, assuming that his name is `{1}'".format(filename or self.title, self.author).decode("utf-8"))

        # manage languages
        self.in_default_lang = True
        if 'DEFAULT_LANG' in settings:
            default_lang = settings['DEFAULT_LANG'].lower()
            if not hasattr(self, 'lang'):
                self.lang = default_lang

            self.in_default_lang = (self.lang == default_lang)

        # create the slug if not existing, fro mthe title
        if not hasattr(self, 'slug') and hasattr(self, 'title'):
            self.slug = slugify(self.title)


        # get a link format for this item
        self.urls = self.default_urls
        # settings will be PAGE_URL for Page, ARTICLE_URL for Article..
        url_setting_key = "%s_URL" % self.__class__.__name__.upper()
        if url_setting_key in settings:
            urls = settings[url_setting_key]
            # allow both a single format, and a (lang, default_lang) format
            if isinstance(urls, (str, unicode)):
               urls = (urls, urls)
            self.urls = urls

        if filename:
            self.filename = filename

        # manage the date format
        if not hasattr(self, 'date_format'):
            if hasattr(self, 'lang') and self.lang in settings['DATE_FORMATS']:
                self.date_format = settings['DATE_FORMATS'][self.lang]
            else:
                self.date_format = settings['DEFAULT_DATE_FORMAT']

        if hasattr(self, 'date'):
            self.locale_date = self.date.strftime(self.date_format.encode('ascii','xmlcharrefreplace')).decode('utf')

        # manage summary
        if not hasattr(self, 'summary'):
            self.summary = property(lambda self: truncate_html_words(self.content, 50)).__get__(self, Page)

        # manage status
        if not hasattr(self, 'status'):
            self.status = settings['DEFAULT_STATUS']

    def check_properties(self):
        """test that each mandatory property is set."""
        for prop in self.mandatory_properties:
            if not hasattr(self, prop):
                raise NameError(prop)

    def _url(self, as_file=False):
        url_format = self.urls[0] if self.in_default_lang else self.urls[1]
        return format_url( url_format, {
            'title': self.slug,
            'slug': self.slug,
            'lang': self.lang,
            'year': self.date.strftime("%Y"),
            'month': self.date.strftime("%m"),
            'day': self.date.strftime("%d"),
        }, add_file_suffix=as_file)

    @property
    def url(self, as_file=False):
        return self._url()

    @property
    def save_as(self):
        return self._url(True)

    @property
    def content(self):
        if hasattr(self, "_get_content"):
            content = self._get_content()
        else:
            content = self._content
        return content


class Article(Page):
    mandatory_properties = ('title', 'date', 'category')
    default_urls = (':title.html', ':title-:lang.html',)


class Quote(Page):
    base_properties = ('author', 'date')


def is_valid_content(content, f):
    try:
        content.check_properties()
        return True
    except NameError, e:
        error(u"Skipping %s: impossible to find informations about '%s'" % (f, e))
        return False
