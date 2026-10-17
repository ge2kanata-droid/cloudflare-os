"""Read-only tests for homepage purchase-link depth classifications."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("hitomazu_funnels_extra", Path(__file__).with_name("check_funnels.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

def page(html):
    p = audit.PageParser()
    p.feed(html)
    return {"status": "fetched", "http_status": 200, "error": None, "title": "test", "parser": p}

class ProductLinkDepthTests(unittest.TestCase):
    def test_known_note_article(self):
        self.assertEqual(audit.classify_sales_link(audit.PAID), "note_article")
        self.assertEqual(audit.classify_sales_link(audit.FREE), "note_article")

    def test_note_profile_not_article(self):
        self.assertEqual(audit.classify_sales_link("https://note.com/open_squid6912"), "note_profile")

    def test_suzuri_individual_digital_and_physical_items(self):
        self.assertEqual(audit.classify_sales_link("https://suzuri.jp/hitomazu-tools/digital_products/159682"), "suzuri_product")
        self.assertEqual(audit.classify_sales_link("https://suzuri.jp/hitomazu-tools/21108492/acrylic-omamori/free/clear"), "suzuri_product")

    def test_suzuri_store_and_category_not_products(self):
        self.assertEqual(audit.classify_sales_link("https://suzuri.jp/hitomazu-tools/"), "suzuri_storefront")
        self.assertEqual(audit.classify_sales_link("https://suzuri.jp/hitomazu-tools/digital_products"), "suzuri_category")

    def test_foreign_urls_are_ignored(self):
        self.assertIsNone(audit.classify_sales_link("https://unrelated.example.com/suzuri.jp/hitomazu-tools"))
        self.assertIsNone(audit.classify_sales_link("javascript:alert(1)"))

    def test_storefront_only_gets_advisory(self):
        data=page('<a href="https://note.com/open_squid6912">note</a>'
                  '<a href="https://suzuri.jp/hitomazu-tools">SUZURI</a>')
        with patch.object(audit, "fetch_html", return_value=data):
            result=audit.check_home()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["link_inventory"]["suzuri_storefront"], 1)
        self.assertIsNotNone(result["link_advisory"])

    def test_direct_product_no_storefront_only_advisory(self):
        data=page('<a href="https://suzuri.jp/hitomazu-tools/digital_products/159682">朝のお守り</a>'
                  '<a href="https://note.com/open_squid6912">note</a>')
        with patch.object(audit, "fetch_html", return_value=data):
            result=audit.check_home()
        self.assertEqual(result["link_inventory"]["suzuri_product"],1)
        self.assertIsNone(result["link_advisory"])

    def test_403_is_unknown_not_a_missing_link(self):
        with patch.object(audit,"fetch_html",return_value={"status":"unknown","http_status":403,"error":"restricted","parser":None}):
            result=audit.check_home()
        self.assertEqual(result["status"],"unknown")
        self.assertIsNone(result["link_inventory"])
        self.assertIsNone(result["link_advisory"])

if __name__ == "__main__":
    unittest.main()
