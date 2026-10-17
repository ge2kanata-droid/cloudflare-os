"""Offline regression tests. No network or API keys required."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).with_name("check_funnels.py")
spec = importlib.util.spec_from_file_location("hitomazu_funnels", MODULE_PATH)
funnel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(funnel)


def fake_html(content):
    parser = funnel.PageParser()
    parser.feed(content)
    return {
        "status": "fetched", "http_status": 200, "error": None,
        "title": "テスト", "parser": parser,
    }


class FunnelAuditTests(unittest.TestCase):
    def test_valid_free_to_paid_link(self):
        page = fake_html('<html><a href="/open_squid6912/n/n4b1b3da8651b"><span>有料版（note・300円）</span></a></html>')
        with patch.object(funnel, "fetch_html", return_value=page):
            result = funnel.check_note(funnel.TARGETS[0])
        self.assertEqual(result["status"], "ok")

    def test_wrong_href_observed(self):
        page = fake_html('<a href="https://suzuri.jp/hitomazu-tools">有料版（note・300円）</a>')
        with patch.object(funnel, "fetch_html", return_value=page):
            result = funnel.check_note(funnel.TARGETS[0])
        self.assertEqual(result["status"], "needs_review")
        self.assertIn("suzuri.jp", result["target_href"])

    def test_missing_anchor_is_unknown_not_failed(self):
        page = fake_html("<html><body>JavaScriptで表示するページ</body></html>")
        with patch.object(funnel, "fetch_html", return_value=page):
            result = funnel.check_note(funnel.TARGETS[0])
        self.assertEqual(result["status"], "unknown")

    def test_inaccessible_403_is_unknown(self):
        with patch.object(funnel, "fetch_html", return_value={
            "status": "unknown", "http_status": 403, "error": "アクセス制限", "title": None, "parser": None
        }):
            result = funnel.check_note(funnel.TARGETS[1])
        self.assertEqual(result["status"], "unknown")

    def test_stale_phrase_ignores_script_text(self):
        page = fake_html("<script>販売する準備をしています</script><a href='"
                         + funnel.FREE + "'>無料版（note・0円）</a>")
        with patch.object(funnel, "fetch_html", return_value=page):
            result = funnel.check_note(funnel.TARGETS[1])
        self.assertEqual(result["status"], "ok")
        self.assertIs(result["stale_phrase"], False)

    def test_stale_phrase_visible_text(self):
        page = fake_html("<p>SUZURIと同じ内容をnoteでも販売する準備をしています</p>")
        with patch.object(funnel, "fetch_html", return_value=page):
            result = funnel.check_note(funnel.TARGETS[1])
        self.assertIs(result["stale_phrase"], True)

    def test_home_counts_note_and_suzuri_links(self):
        page = fake_html("<a href='https://note.com/open_squid6912'>Note</a>"
                         "<a href='https://suzuri.jp/hitomazu-tools'>SUZURI</a>")
        with patch.object(funnel, "fetch_html", return_value=page):
            result = funnel.check_home()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["note_links"], 1)
        self.assertEqual(result["suzuri_links"], 1)


if __name__ == "__main__":
    unittest.main()
