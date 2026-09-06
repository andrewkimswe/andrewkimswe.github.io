#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://andrewkimswe.github.io"
INDEXABLE_PAGES = ("index.html", "articles.html", "projects.html")
HOME_RECENT_LIMIT = 7
REQUIRED_META = (
    "description",
    "og:title",
    "og:description",
    "og:type",
    "og:url",
    "og:image",
    "og:image:type",
    "og:image:width",
    "og:image:height",
    "og:image:alt",
    "twitter:card",
    "twitter:title",
    "twitter:description",
    "twitter:image",
    "twitter:image:alt",
)


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.resources: list[str] = []
        self.post_row_links: list[str] = []
        self.post_rows: list[dict[str, str]] = []
        self.meta: list[dict[str, str]] = []
        self.link_tags: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.ids: list[str] = []
        self.h1_count = 0
        self.article_h2_ids: list[str] = []
        self.toc_links: list[str] = []
        self.title_parts: list[str] = []
        self._capture_title = False
        self._post_row_depth = 0
        self._article_body_depth = 0
        self._toc_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        classes = set(data.get("class", "").split())

        if tag == "title":
            self._capture_title = True
        if tag == "article" and "post-row" in classes:
            self._post_row_depth += 1
            self.post_rows.append(data)
        if tag == "div":
            if self._article_body_depth:
                self._article_body_depth += 1
            elif "article-body" in classes:
                self._article_body_depth = 1
        if tag == "aside" and "article-toc" in classes:
            self._toc_depth += 1

        element_id = data.get("id")
        if element_id:
            self.ids.append(element_id)
        if tag == "a" and data.get("href"):
            href = data["href"]
            self.links.append(href)
            if self._post_row_depth:
                self.post_row_links.append(href)
            if self._toc_depth:
                self.toc_links.append(href)
        if tag in {"img", "script"} and data.get("src"):
            self.resources.append(data["src"])
        if tag == "img":
            self.images.append(data)
        if tag == "meta":
            self.meta.append(data)
        if tag == "link":
            self.link_tags.append(data)
            if data.get("rel") == "stylesheet" and data.get("href"):
                self.resources.append(data["href"])
        if tag == "h1":
            self.h1_count += 1
        if tag == "h2" and self._article_body_depth and element_id:
            self.article_h2_ids.append(element_id)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._capture_title = False
        if tag == "article" and self._post_row_depth:
            self._post_row_depth -= 1
        if tag == "div" and self._article_body_depth:
            self._article_body_depth -= 1
        if tag == "aside" and self._toc_depth:
            self._toc_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self.title_parts.append(data)

    @property
    def title(self) -> str:
        return " ".join(part.strip() for part in self.title_parts if part.strip())


def parse_html(path: Path) -> SiteParser:
    parser = SiteParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def meta_values(parsed: SiteParser) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for item in parsed.meta:
        key = item.get("property") or item.get("name")
        if key:
            values.setdefault(key, []).append(item.get("content", ""))
    return values


def canonical_values(parsed: SiteParser) -> list[str]:
    return [
        item.get("href", "")
        for item in parsed.link_tags
        if "canonical" in item.get("rel", "").split()
    ]


def expected_url(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return f"{SITE_URL}/" if relative == "index.html" else f"{SITE_URL}/{relative}"


def local_target(source: Path, raw_url: str) -> tuple[Path, str] | None:
    if raw_url.startswith("//"):
        return None
    parts = urlsplit(raw_url)
    if parts.scheme in {"mailto", "tel", "data", "javascript"}:
        return None
    if parts.scheme in {"http", "https"}:
        if f"{parts.scheme}://{parts.netloc}" != SITE_URL:
            return None
        raw_path = parts.path
    elif parts.scheme or parts.netloc:
        return None
    else:
        raw_path = parts.path

    decoded = unquote(raw_path)
    if not decoded:
        target = source
    elif decoded.startswith("/"):
        target = ROOT / decoded.lstrip("/")
    else:
        target = source.parent / decoded

    target = target.resolve()
    if decoded.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target, unquote(parts.fragment)


def validate_page(path: Path, parsed: SiteParser, errors: list[str], is_post: bool = False) -> None:
    label = path.relative_to(ROOT)
    values = meta_values(parsed)

    if not parsed.title:
        fail(f"{label} is missing a document title", errors)
    if parsed.h1_count != 1:
        fail(f"{label} should have exactly one h1, found {parsed.h1_count}", errors)

    duplicate_ids = sorted(item for item, count in Counter(parsed.ids).items() if count > 1)
    if duplicate_ids:
        fail(f"{label} has duplicate ids: {duplicate_ids}", errors)

    for key in REQUIRED_META:
        entries = values.get(key, [])
        if len(entries) != 1 or not entries[0].strip():
            fail(f"{label} should have exactly one non-empty {key}, found {len(entries)}", errors)

    canonicals = canonical_values(parsed)
    if canonicals != [expected_url(path)]:
        fail(f"{label} has an invalid canonical URL: {canonicals}", errors)
    if values.get("og:url") != [expected_url(path)]:
        fail(f"{label} has an invalid og:url: {values.get('og:url', [])}", errors)

    if is_post:
        for key in ("article:published_time", "article:modified_time"):
            entries = values.get(key, [])
            if len(entries) != 1 or not entries[0].strip():
                fail(f"{label} should have exactly one non-empty {key}", errors)
        expected_toc = [f"#{heading_id}" for heading_id in parsed.article_h2_ids]
        if parsed.toc_links != expected_toc:
            fail(f"{label} TOC does not match article headings", errors)

    for image in parsed.images:
        classes = set(image.get("class", "").split())
        if "alt" not in image:
            fail(f"{label} has an image without alt text", errors)
        elif not image["alt"].strip() and "tracking-pixel" not in classes:
            fail(f"{label} has a non-tracking image with empty alt text", errors)


def validate_internal_targets(
    source: Path,
    parsed: SiteParser,
    parsed_pages: dict[Path, SiteParser],
    errors: list[str],
) -> None:
    for raw_url in (*parsed.links, *parsed.resources):
        target_info = local_target(source, raw_url)
        if target_info is None:
            continue
        target, fragment = target_info
        label = source.relative_to(ROOT)
        if not target.is_relative_to(ROOT.resolve()):
            fail(f"{label} points outside the site root: {raw_url}", errors)
            continue
        if not target.exists():
            fail(f"{label} has a missing local target: {raw_url}", errors)
            continue
        if fragment and target.suffix == ".html":
            target_parser = parsed_pages.get(target)
            if target_parser is None:
                target_parser = parse_html(target)
                parsed_pages[target] = target_parser
            if fragment not in target_parser.ids:
                fail(f"{label} points to a missing fragment: {raw_url}", errors)


def main() -> int:
    errors: list[str] = []
    post_paths = sorted((ROOT / "posts").glob("*.html"))
    post_files = [path.name for path in post_paths]
    page_paths = [ROOT / name for name in INDEXABLE_PAGES]
    parsed_pages = {
        path.resolve(): parse_html(path)
        for path in (*page_paths, *post_paths, ROOT / "404.html")
    }

    for path in page_paths:
        validate_page(path, parsed_pages[path.resolve()], errors)
    for path in post_paths:
        validate_page(path, parsed_pages[path.resolve()], errors, is_post=True)

    not_found = parsed_pages[(ROOT / "404.html").resolve()]
    if not_found.h1_count != 1:
        fail(f"404.html should have exactly one h1, found {not_found.h1_count}", errors)
    if "noindex" not in " ".join(meta_values(not_found).get("robots", [])):
        fail("404.html must be noindex", errors)

    articles = parsed_pages[(ROOT / "articles.html").resolve()]
    article_links = [
        link.removeprefix("./posts/")
        for link in articles.post_row_links
        if link.startswith("./posts/")
    ]
    if sorted(article_links) != post_files or len(article_links) != len(set(article_links)):
        fail("articles.html must list every post exactly once", errors)
    for index, row in enumerate(articles.post_rows, start=1):
        if not row.get("data-tags") or not row.get("data-title") or not row.get("data-summary"):
            fail(f"articles.html post row {index} is missing search data", errors)

    home = parsed_pages[(ROOT / "index.html").resolve()]
    home_links = [
        link.removeprefix("./posts/")
        for link in home.post_row_links
        if link.startswith("./posts/")
    ]
    dated_posts = []
    now = datetime.now(timezone.utc)
    for path in post_paths:
        published = meta_values(parsed_pages[path.resolve()]).get("article:published_time", [""])[0]
        dated_posts.append((published, path.name))
        try:
            published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            fail(f"{path.relative_to(ROOT)} has an invalid publication timestamp", errors)
            continue
        if published_at.tzinfo is None or published_at.utcoffset() is None:
            fail(f"{path.relative_to(ROOT)} publication timestamp must include a timezone", errors)
        elif published_at.astimezone(timezone.utc) > now:
            fail(
                f"{path.relative_to(ROOT)} is future-dated; move it to scheduled/ until publication",
                errors,
            )
    expected_recent = [name for _, name in sorted(dated_posts, reverse=True)[:HOME_RECENT_LIMIT]]
    if home_links != expected_recent:
        fail(f"index.html recent posts are stale: expected {expected_recent}, found {home_links}", errors)

    try:
        feed = ET.parse(ROOT / "feed.xml")
        feed_posts = sorted(
            link.text.rsplit("/", 1)[-1]
            for link in feed.findall("./channel/item/link")
            if link.text
        )
        if feed_posts != post_files:
            fail(f"feed.xml items differ from posts directory: {set(post_files) ^ set(feed_posts)}", errors)
    except ET.ParseError as exc:
        fail(f"feed.xml is invalid XML: {exc}", errors)

    try:
        sitemap = ET.parse(ROOT / "sitemap.xml")
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [loc.text or "" for loc in sitemap.findall("./sm:url/sm:loc", ns)]
        sitemap_posts = sorted(loc.rsplit("/", 1)[-1] for loc in locations if "/posts/" in loc)
        if sitemap_posts != post_files:
            fail(f"sitemap.xml urls differ from posts directory: {set(post_files) ^ set(sitemap_posts)}", errors)
        for required in (f"{SITE_URL}/", f"{SITE_URL}/articles.html", f"{SITE_URL}/projects.html"):
            if required not in locations:
                fail(f"sitemap.xml is missing {required}", errors)
    except ET.ParseError as exc:
        fail(f"sitemap.xml is invalid XML: {exc}", errors)

    for path, parsed in list(parsed_pages.items()):
        validate_internal_targets(path, parsed, parsed_pages, errors)

    for path in post_paths:
        source = path.read_text(encoding="utf-8")
        if "SAA" in source or "시험에서는" in source:
            fail(f"{path.relative_to(ROOT)} contains exam-oriented editorial language", errors)

    if errors:
        print("Site validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Site validation passed for {len(post_files)} posts and {len(page_paths)} indexable pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
