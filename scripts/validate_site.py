#!/usr/bin/env python3
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://andrewkimswe.github.io"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.post_row_links: list[str] = []
        self.meta: list[dict[str, str]] = []
        self.h1_count = 0
        self._post_row_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        classes = set(data.get("class", "").split())
        if "post-row" in classes:
            self._post_row_depth += 1
        if tag == "a" and data.get("href"):
            self.links.append(data["href"])
            if self._post_row_depth:
                self.post_row_links.append(data["href"])
        if tag == "meta":
            self.meta.append(data)
        if tag == "h1":
            self.h1_count += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "article" and self._post_row_depth:
            self._post_row_depth -= 1


def parse_html(path: Path) -> LinkParser:
    parser = LinkParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    post_files = sorted(path.name for path in (ROOT / "posts").glob("*.html"))

    index = parse_html(ROOT / "index.html")
    index_posts = sorted(link.removeprefix("./posts/") for link in index.post_row_links if link.startswith("./posts/"))
    if index_posts != post_files:
        fail(f"index.html post links differ from posts directory: {set(post_files) ^ set(index_posts)}", errors)

    feed = ET.parse(ROOT / "feed.xml")
    feed_posts = sorted(link.text.rsplit("/", 1)[-1] for link in feed.findall("./channel/item/link") if link.text)
    if feed_posts != post_files:
        fail(f"feed.xml items differ from posts directory: {set(post_files) ^ set(feed_posts)}", errors)

    sitemap = ET.parse(ROOT / "sitemap.xml")
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_posts = sorted(
        loc.text.rsplit("/", 1)[-1]
        for loc in sitemap.findall("./sm:url/sm:loc", ns)
        if loc.text and "/posts/" in loc.text
    )
    if sitemap_posts != post_files:
        fail(f"sitemap.xml urls differ from posts directory: {set(post_files) ^ set(sitemap_posts)}", errors)

    for path in sorted((ROOT / "posts").glob("*.html")) + [ROOT / "index.html"]:
        parsed = parse_html(path)
        meta = {(item.get("property") or item.get("name")): item.get("content", "") for item in parsed.meta}
        if parsed.h1_count != 1:
            fail(f"{path.relative_to(ROOT)} should have exactly one h1, found {parsed.h1_count}", errors)
        for key in ("description", "og:image", "twitter:image"):
            if not meta.get(key):
                fail(f"{path.relative_to(ROOT)} is missing {key}", errors)
        for key in ("og:image", "twitter:card", "twitter:image"):
            count = sum(1 for item in parsed.meta if (item.get("property") or item.get("name")) == key)
            if count != 1:
                fail(f"{path.relative_to(ROOT)} should have exactly one {key}, found {count}", errors)
        if path.name != "index.html" and not meta.get("article:published_time"):
            fail(f"{path.relative_to(ROOT)} is missing article:published_time", errors)

    for path in ROOT.glob("*.xml"):
        ET.parse(path)

    if errors:
        print("Site validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Site validation passed for {len(post_files)} posts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
