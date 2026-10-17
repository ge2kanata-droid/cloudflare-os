#!/usr/bin/env python3
"""No-API-key, read-only daily audit of PUBLIC Hitomazu landing pages.

This script does not publish, purchase, authenticate, or access private analytics.
An HTTP 403/429 or network error is 'unknown' (not proof the website is down).
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SITES = [
    ("ひとまず道具店 公式HP", "https://hitomazu-tools-home.pages.dev/"),
    ("ひとまず仕分け", "https://hitomazu-shiwake.netlify.app/"),
]
LINK_HOSTS = ("note.com", "suzuri.jp")
MAX_BYTES = 512_000


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "title":
            self._in_title = True

    def handle_data(self, data):
        if self._in_title:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


def check(name, url):
    result = {
        "name": name, "url": url, "result": "unknown",
        "http_status": None, "note": "未取得",
        "title": None, "sales_links": {"note.com": 0, "suzuri.jp": 0},
        "findings": [],
    }
    try:
        req = Request(url, headers={"User-Agent": "HitomazuPublicSiteAudit/0.1 (read-only; GitHub Actions)"})
        with urlopen(req, timeout=14) as response:
            code = response.getcode()
            result["http_status"] = code
            result["note"] = "ページが応答しました"
            result["result"] = "reachable" if 200 <= code < 400 else "unknown"
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type.lower() and 200 <= code < 300:
                raw = response.read(MAX_BYTES)
                parser = LinkParser()
                parser.feed(raw.decode("utf-8", errors="replace"))
                result["title"] = parser.title.strip()[:160]
                for host in LINK_HOSTS:
                    result["sales_links"][host] = sum(host in link.lower() for link in parser.links)
                if sum(result["sales_links"].values()) == 0:
                    result["findings"].append("トップページの直接リンクにはnote/SUZURIが見つかりません（JS生成や別ページのリンクは判定不可）")
    except HTTPError as ex:
        result["http_status"] = ex.code
        result["note"] = "HTTP応答あり。bot対策・一時制限の可能性があるため手動確認が必要"
    except (URLError, TimeoutError, OSError) as ex:
        result["note"] = "ネットワークから取得できません（サイト停止とは限りません）"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="site-status.json")
    args = parser.parse_args()
    report = {
        "schema": 1, "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "checks": [check(name, url) for name, url in SITES],
        "notice": "公開ページのHTML簡易点検です。非公開の売上・訪問者データは取得しません。",
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Created", path)
    for item in report["checks"]:
        print(item["name"], item["result"], item["http_status"], item["sales_links"])


if __name__ == "__main__":
    main()
