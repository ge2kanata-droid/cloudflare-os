#!/usr/bin/env python3
"""Read-only funnel monitor for already-published Hitomazu Tools pages.

Uses only Python stdlib and publicly accessible HTML. Produces observations,
never changes products, drafts, credentials or third-party pages. A blocked
request or JS-only page is UNKNOWN, never fabricated failure or zero sales.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

FREE = "https://note.com/open_squid6912/n/n1c07a17a68c7"
PAID = "https://note.com/open_squid6912/n/n4b1b3da8651b"
HOME = "https://hitomazu-tools-home.pages.dev/"
SHIWAKE = "https://hitomazu-shiwake.netlify.app/"
TARGETS = [
    {"id": "ht022-free", "name": "001 無料note → 有料note", "url": FREE, "expected": PAID,
     "anchor_label": "有料版（note・300円）", "owner": "HT-022：既存note担当", "notion_ref": "HT-022"},
    {"id": "ht022-paid", "name": "001 有料note → 無料note", "url": PAID, "expected": FREE,
     "anchor_label": "無料版（note・0円）", "owner": "HT-022：既存note担当", "notion_ref": "HT-022"},
]
MAX_HTML = 650_000
MAX_LINKS = 400


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts = []
        self.visible_parts = []
        self.anchors = []
        self._skip = 0
        self._title = 0
        self._anchor = None

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if tag in ("script", "style", "noscript", "svg", "template"):
            self._skip += 1
        if tag == "title":
            self._title += 1
        if tag == "a" and not self._skip:
            # The HTML page may include many nested nodes inside links.
            self._anchor = {"href": props.get("href", ""), "text": ""}

    def handle_data(self, data):
        if self._title:
            self.title_parts.append(data)
        if not self._skip:
            self.visible_parts.append(data)
            if self._anchor is not None:
                self._anchor["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._anchor is not None:
            if len(self.anchors) < MAX_LINKS:
                self._anchor["text"] = re.sub(r"\s+", " ", self._anchor["text"]).strip()
                self.anchors.append(self._anchor)
            self._anchor = None
        if tag == "title":
            self._title = max(0, self._title - 1)
        if tag in ("script", "style", "noscript", "svg", "template"):
            self._skip = max(0, self._skip - 1)

    @property
    def visible(self):
        return re.sub(r"\s+", " ", " ".join(self.visible_parts))


def normalized(url):
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if parts.scheme not in ("http", "https") or not host:
            return None
        return host.removeprefix("www.") + parts.path.rstrip("/")
    except ValueError:
        return None


def fetch_html(url):
    result = {"status": "unknown", "http_status": None, "error": None,
              "title": None, "parser": None}
    request = Request(url, headers={"User-Agent": "HitomazuToolsReadOnlyAudit/0.2",
                                     "Accept": "text/html,application/xhtml+xml"})
    try:
        with urlopen(request, timeout=12) as response:
            status = response.status
            result["http_status"] = status
            if status < 200 or status >= 300:
                result["error"] = "非200応答のため本文未検査"
                return result
            kind = response.headers.get("Content-Type", "")
            if "text/html" not in kind.lower() and "application/xhtml+xml" not in kind.lower():
                result["error"] = "HTML以外のコンテンツ"
                return result
            raw = response.read(MAX_HTML + 1)
            if len(raw) > MAX_HTML:
                result["error"] = "HTMLが容量制限を超えました"
                return result
            parser = PageParser()
            parser.feed(raw.decode("utf-8", errors="replace"))
            result["parser"] = parser
            result["status"] = "fetched"
            result["title"] = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()[:120]
    except HTTPError as exc:
        result["http_status"] = exc.code
        result["error"] = "閲覧制限・一時的エラーの可能性" if exc.code in (401, 403, 429, 503) else "HTTP応答エラー"
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        result["error"] = "ネットワーク取得不可（公開ページが停止したとは限りません）"
    return result


def check_note(target):
    page = fetch_html(target["url"])
    record = {key: target[key] for key in
              ("id", "name", "url", "expected", "anchor_label", "owner", "notion_ref")}
    record.update(status="unknown", http_status=page["http_status"],
                  target_href=None, page_title=page["title"], evidence="",
                  stale_phrase=None)
    if page["status"] != "fetched":
        record["evidence"] = page["error"] or "公開HTMLの取得失敗"
        return record

    parser = page["parser"]
    label = target["anchor_label"].replace(" ", "")
    anchor_matches = [a for a in parser.anchors if label in re.sub(r"\s+", "", a["text"])]
    if not anchor_matches:
        record["evidence"] = "対象の案内文をHTMLのリンク要素で確認できません（JS描画の可能性あり）"
    else:
        links = [urljoin(target["url"], a["href"]) for a in anchor_matches if a["href"]]
        expected = normalized(target["expected"])
        if any(normalized(x) == expected for x in links):
            record["status"] = "ok"
            record["target_href"] = target["expected"]
            record["evidence"] = "対象案内文から正しいnote記事へリンク"
        elif links:
            record["status"] = "needs_review"
            record["target_href"] = links[0][:400]
            record["evidence"] = "案内文のリンク先が期待するnote記事ではありません"
        else:
            record["status"] = "needs_review"
            record["evidence"] = "案内文は存在しますがhrefがありません"

    if target["id"] == "ht022-paid":
        # The phrase was recorded in the existing task register as outdated.
        record["stale_phrase"] = ("販売する準備をしています" in parser.visible)
    return record


def check_home():
    result = {"url": HOME, "status": "unknown", "http_status": None,
              "note_links": None, "suzuri_links": None, "evidence": ""}
    response = fetch_html(HOME)
    result["http_status"] = response["http_status"]
    if response["status"] != "fetched":
        result["evidence"] = response["error"] or "確認不可"
        return result
    links = [urljoin(HOME, a["href"]) for a in response["parser"].anchors if a["href"]]
    result["note_links"] = sum(urlsplit(link).hostname in ("note.com", "www.note.com") for link in links)
    result["suzuri_links"] = sum(urlsplit(link).hostname in ("suzuri.jp", "www.suzuri.jp") for link in links)
    result["status"] = "ok" if (result["note_links"] + result["suzuri_links"]) > 0 else "needs_review"
    result["evidence"] = ("トップページのHTMLの直接リンクのみを数えています。"
                          "JS描画・別ページ・購入成否は検査対象外。")
    return result


def collect_report():
    note_checks = [check_note(t) for t in TARGETS]
    home = check_home()
    findings = []
    for record in note_checks:
        if record["status"] == "needs_review":
            findings.append({
                "id": record["id"], "severity": "high",
                "title": record["name"] + "：リンク先の再確認",
                "details": record["evidence"], "owner": record["owner"],
                "url": record["url"], "observed_href": record["target_href"],
                "action": "既存のHT-022担当へ検証結果を共有。保存失敗の問題が解消するまで公開記事を上書きしない。",
                "note": "確認結果は公開HTML上のみ。既存担当・Notionの工程ステータスを変更しません。"
            })
        if record["stale_phrase"] is True:
            findings.append({
                "id": "ht022-stale-copy", "severity": "normal",
                "title": "001 有料note：販売準備中という旧表現",
                "details": "公開HTMLの可視テキストに旧文言を検出",
                "owner": "HT-022：既存note担当", "url": record["url"],
                "action": "担当が既に認識している差分。重複記事作成は禁止。",
            })
    if home["status"] == "needs_review":
        findings.append({
            "id": "hp-store-links", "severity": "normal",
            "title": "公式HP：販売先リンクの要確認",
            "details": "トップページのHTMLからnote・SUZURI直接リンクを確認できず",
            "owner": "HT-043：既存Web担当", "url": HOME,
            "action": "HTML生成・別ページリンクの可能性を含め、担当が確認する。"
        })
    summary = {
        "needs_review": sum(x["status"] == "needs_review" for x in note_checks) + (home["status"] == "needs_review"),
        "verified_ok": sum(x["status"] == "ok" for x in note_checks) + (home["status"] == "ok"),
        "unknown": sum(x["status"] == "unknown" for x in note_checks) + (home["status"] == "unknown"),
        "findings": len(findings)
    }
    return {
        "schema": 1, "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": summary, "notion_last_checked": "2026-10-17",
        "source": "公開ページのHTMLのみ（Notion・販売管理画面は読み取りません）",
        "sites": [home], "note_checks": note_checks, "findings": findings,
        "limits": ["外部への書き込み・購入は一切行いません",
                   "403・429やJS生成ページの結果は不明として扱います",
                   "実際のクリック数・販売数・購入率は収集できません",
                   "既存HT-022・HT-043の担当作業を再登録しません"],
    }


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--output", default="funnel-status.json")
    args = cli.parse_args()
    report = collect_report()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Revenue-funnel audit", report["checked_at"], report["summary"])
    for x in report["note_checks"]:
        print(x["id"], x["status"], x["http_status"], x["evidence"])


if __name__ == "__main__":
    main()
