
# Join URLs that use "gemini://" rather than "http://"

# There are some tools in the standard Python libraries for joining URLs and
# dealing with relative URLs and so on, but on a brief investigation they
# seem to misbehave when given "gemini://" URLs. This may be a misunderstanding
# on my part, but in any case I have hacked together this module to work around
# this (perceived) issue.
#
# Specifically, it seemed that urllib.parse.urljoin didn't like gemini:// URLs.

import urllib.parse
import urllib3
import unittest


def gemini_urljoin(base, url):
    """
    Return a new URL, which would be obtained if `url` were interpreted
    relative to `base`, e.g., where a browser were viewing the page at `base`
    and clicked on a link to `url`.

    e.g.: base=gemini://some.domain.com/dir1/index.gemini
          rel=other-page.gemini
            --> gemini://some.domain.com/dir1/other-page.gemini

    If `base` is None, then just return `url`.
    If `base` or `url` has a scheme other than "gemini://" reject it
    """
    if base is None:
        return url
    
    assert get_scheme(base) in [None, "gemini"]
    if get_scheme(url) not in [None, "gemini"]:
        return url

    tmp = httpise_url(base)
    result = urllib.parse.urljoin(tmp, url)
    return unhttpise_url(result)

def same_host(url):
    u = urllib3.util.parse_url(url)
    return u.host is None

def get_scheme(url):
    return urllib3.util.parse_url(url).scheme

def has_scheme(url):
    return get_scheme(url) is not None

def change_scheme(url, scheme):
    parts = list(urllib.parse.urlsplit(url))
    parts[0] = scheme
    return urllib.parse.urlunsplit(tuple(parts))

def httpise_url(url):
    return change_scheme(url, "http")

def unhttpise_url(url):
    return change_scheme(url, "gemini")


class TestUrlHacks(unittest.TestCase):
    def test_urljoin(self):
        data = [
            ("gemini://host.domain.tld/dir1/file2",
             "file3",
             "gemini://host.domain.tld/dir1/file3"),

            (None,
             "example.gmi",
             "example.gmi"),

            ("gemini://a.com/b/c.txt",
             "../d.txt",
             "gemini://a.com/d.txt"),

            ("gemini://a.com/b",
             "gemini://b.com/c",
             "gemini://b.com/c")
            ]

        for datum in data:
            base, url, expected_result = datum
            with self.subTest(i=datum):
                actual_result = gemini_urljoin(base, url)
                self.assertEqual(actual_result, expected_result)
