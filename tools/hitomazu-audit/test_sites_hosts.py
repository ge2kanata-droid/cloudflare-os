"""Count only actual external sales destinations in publicly rendered HTML."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("hitomazu_sites", Path(__file__).with_name("check_sites.py"))
sites = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sites)

class HostTests(unittest.TestCase):
    def test_valid_links(self):
        base = "https://hitomazu-tools-home.pages.dev/"
        self.assertEqual(sites.sales_host("https://note.com/open_squid6912/n/n4b1b3da8651b", base), "note.com")
        self.assertEqual(sites.sales_host("https://www.suzuri.jp/hitomazu-tools", base), "suzuri.jp")
        self.assertEqual(sites.sales_host("https://NOTE.COM/abc", base), "note.com")

    def test_spoofed_names_are_not_sales_destinations(self):
        base = "https://hitomazu-tools-home.pages.dev/"
        for value in ("https://example.org/note.com/thing", "https://evilnote.com/",
                      "https://suzuri.jp.evil.org/x", "/go?url=https://note.com/product",
                      "https://evil.org/?shop=suzuri.jp", "mailto:owner@note.com",
                      "javascript:alert('note.com')"):
            self.assertIsNone(sites.sales_host(value, base), value)

    def test_relative_non_sales_links_ignored(self):
        self.assertIsNone(sites.sales_host("/index.html", "https://hitomazu-tools-home.pages.dev/"))

if __name__ == "__main__":
    unittest.main()
