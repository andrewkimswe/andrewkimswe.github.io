#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.utils import format_datetime
from html import escape, unescape
from math import ceil
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://andrewkimswe.github.io"
SITE_NAME = "Jiwon Kim | Engineering Notes"
TITLE_SUFFIX = "Jiwon Kim Engineering Notes"
SOCIAL_IMAGE = f"{SITE_URL}/assets/social-card.png"
HOME_RECENT_LIMIT = 7
ASSET_VERSION = "20260905-4"
GENERIC_RELATED_TAGS = {"aws", "cloud", "architecture", "operations"}


@dataclass(frozen=True)
class Post:
    path: Path
    slug: str
    title: str
    page_title: str
    description: str
    summary: str
    date: datetime
    modified: datetime
    tags: tuple[str, ...]
    topic: str
    data_tags: str
    reading_minutes: int

    @property
    def url(self) -> str:
        return f"{SITE_URL}/posts/{self.slug}"

    @property
    def display_date(self) -> str:
        return self.date.strftime("%Y.%m.%d")

    @property
    def iso_date(self) -> str:
        return self.date.strftime("%Y-%m-%d")

    @property
    def rss_date(self) -> str:
        return format_datetime(self.date)

    @property
    def modified_iso_date(self) -> str:
        return self.modified.strftime("%Y-%m-%d")


def collapse(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def strip_tags(value: str) -> str:
    return collapse(re.sub(r"<[^>]+>", " ", value))


def match_one(pattern: str, text: str, default: str = "") -> str:
    match = re.search(pattern, text, re.S)
    return collapse(match.group(1)) if match else default


def parse_post(path: Path) -> Post:
    html = path.read_text(encoding="utf-8")
    page_title = match_one(r"<title>(.*?)</title>", html).replace(f" | {SITE_NAME}", "")
    page_title = page_title.replace(f" | {TITLE_SUFFIX}", "")
    page_title = page_title.replace(" | Jiwon Kim's Blog", "")
    title = match_one(r'<meta\s+property="og:title"\s+content="([^"]+)"', html, page_title)
    description = match_one(r'<meta\s+name="description"\s+content="([^"]+)"', html)
    summary = match_one(r'<meta\s+property="og:description"\s+content="([^"]+)"', html)
    if not summary:
        summary = strip_tags(match_one(r'<p class="article-summary">\s*(.*?)\s*</p>', html, description))

    published = match_one(r'<meta\s+property="article:published_time"\s+content="([^"]+)"', html)
    if not published:
        published = match_one(r'<time\s+datetime="([^"]+)"', html)
    date = datetime.fromisoformat(published.replace("Z", "+00:00"))

    modified_raw = match_one(r'<meta\s+property="article:modified_time"\s+content="([^"]+)"', html)
    if not modified_raw:
        modified_raw = match_one(r'"dateModified":\s*"([^"]+)"', html, published)
    modified = datetime.fromisoformat(modified_raw.replace("Z", "+00:00"))

    tags = tuple(re.findall(r'<meta\s+property="article:tag"\s+content="([^"]+)"', html))
    eyebrow = match_one(r'<p class="eyebrow">(.*?)</p>', html)
    data_terms = set(tags)
    data_terms.update(part.strip() for part in eyebrow.split("·") if part.strip())
    data_terms.update(term for term in ("AWS", "Cloud", "Architecture", "Operations") if term in html)
    data_terms.update(re.findall(r"[A-Za-z][A-Za-z0-9@+-]*", title))

    body_match = re.search(r'<div class="article-body">(.*?)\n        </div>', html, re.S)
    body_text = strip_tags(body_match.group(1)) if body_match else description
    reading_minutes = max(3, ceil(len(body_text) / 600))

    topic = choose_topic(tags, eyebrow, title)
    return Post(
        path=path,
        slug=path.name,
        title=title,
        page_title=page_title,
        description=description,
        summary=summary,
        date=date,
        modified=modified,
        tags=tags,
        topic=topic,
        data_tags=" | ".join(sorted(data_terms, key=str.lower)),
        reading_minutes=reading_minutes,
    )


def choose_topic(tags: tuple[str, ...], eyebrow: str, title: str) -> str:
    haystack = " ".join((*tags, eyebrow, title))
    if re.search(r"(?<![A-Za-z0-9])DR(?![A-Za-z0-9])", haystack):
        return "DR"
    for label in (
        "Networking",
        "API",
        "S3",
        "FinOps",
        "RAG",
        "LLM",
        "Serverless",
        "Kubernetes",
        "Auto Scaling",
        "Database",
        "Data",
        "Security",
        "Storage",
    ):
        if label.lower() in haystack.lower():
            return label
    return "Cloud" if "AWS" in tags or "Cloud" in haystack else "Architecture"


def load_posts() -> list[Post]:
    return sorted(
        (parse_post(path) for path in (ROOT / "posts").glob("*.html")),
        key=lambda post: (post.date, post.slug),
        reverse=True,
    )


def render_post_rows(posts: list[Post], href_prefix: str = "./posts/") -> str:
    rows = []
    for post in posts:
        rows.append(
            f'''          <article
            class="post-row"
            data-tags="{escape(post.data_tags, quote=True)}"
            data-title="{escape(post.title, quote=True)}"
            data-summary="{escape(post.summary, quote=True)}"
          >
            <a href="{href_prefix}{post.slug}">
              <time datetime="{post.iso_date}">{post.display_date}</time>
              <span class="post-topic">{escape(post.topic)}</span>
              <h3>{escape(post.title)}</h3>
              <p>{escape(post.summary)}</p>
            </a>
          </article>'''
        )
    return "\n".join(rows)


def replace_generated_block(html: str, name: str, content: str) -> str:
    pattern = re.compile(
        rf'(?P<indent>^[ \t]*)<!-- GENERATED:{re.escape(name)}:START -->.*?'
        rf'^[ \t]*<!-- GENERATED:{re.escape(name)}:END -->',
        re.S | re.M,
    )

    def replacement(match: re.Match[str]) -> str:
        indent = match.group("indent")
        return (
            f"{indent}<!-- GENERATED:{name}:START -->\n"
            f"{content}\n"
            f"{indent}<!-- GENERATED:{name}:END -->"
        )

    updated, count = pattern.subn(replacement, html, count=1)
    if count != 1:
        raise ValueError(f"Missing generated block {name}")
    return updated


def update_post_counts(html: str, count: int) -> str:
    pattern = re.compile(
        r'(<(?:span|strong|dd)\b[^>]*\bdata-post-count\b[^>]*>).*?(</(?:span|strong|dd)>)',
        re.S,
    )
    return pattern.sub(lambda match: f"{match.group(1)}{count}{match.group(2)}", html)


def update_listing_pages(posts: list[Post]) -> None:
    index_path = ROOT / "index.html"
    index_html = index_path.read_text(encoding="utf-8")
    index_html = replace_generated_block(
        index_html,
        "RECENT_POSTS",
        render_post_rows(posts[:HOME_RECENT_LIMIT]),
    )
    index_path.write_text(update_post_counts(index_html, len(posts)), encoding="utf-8")

    articles_path = ROOT / "articles.html"
    articles_html = articles_path.read_text(encoding="utf-8")
    articles_html = replace_generated_block(
        articles_html,
        "ALL_POSTS",
        render_post_rows(posts),
    )
    articles_path.write_text(update_post_counts(articles_html, len(posts)), encoding="utf-8")


def remove_meta(html: str, key: str) -> str:
    pattern = re.compile(
        rf'\n\s*<meta\s+(?:property|name)="{re.escape(key)}"\s+content="[^"]*"\s*/>',
        re.S,
    )
    return pattern.sub("", html)


def ensure_social_meta(html: str) -> str:
    for key in (
        "og:image",
        "og:image:type",
        "og:image:width",
        "og:image:height",
        "og:image:alt",
        "twitter:card",
        "twitter:image",
        "twitter:image:alt",
    ):
        html = remove_meta(html, key)

    image_meta = (
        f'    <meta property="og:image" content="{SOCIAL_IMAGE}" />\n'
        f'    <meta property="og:image:type" content="image/png" />\n'
        f'    <meta property="og:image:width" content="1200" />\n'
        f'    <meta property="og:image:height" content="630" />\n'
        f'    <meta property="og:image:alt" content="Jiwon Kim Engineering Notes" />\n'
        f'    <meta name="twitter:card" content="summary_large_image" />\n'
        f'    <meta name="twitter:image" content="{SOCIAL_IMAGE}" />\n'
        f'    <meta name="twitter:image:alt" content="Jiwon Kim Engineering Notes" />'
    )
    pattern = re.compile(
        r'(<meta\s+property="og:url"\s+content="[^"]+"\s*/>)',
        re.S,
    )
    html, count = pattern.subn(lambda match: f"{match.group(1)}\n{image_meta}", html, count=1)
    if count != 1:
        raise ValueError("Post is missing og:url")
    return html


def ensure_post_meta(html: str, post: Post) -> str:
    html = ensure_social_meta(html)
    for key in ("twitter:title", "twitter:description", "article:modified_time"):
        html = remove_meta(html, key)

    metadata = (
        f'\n    <meta name="twitter:title" content="{escape(post.title, quote=True)}" />'
        f'\n    <meta name="twitter:description" content="{escape(post.summary, quote=True)}" />'
        f'\n    <meta property="article:modified_time" content="{post.modified.isoformat()}" />'
    )
    marker = f'    <meta name="twitter:image" content="{SOCIAL_IMAGE}" />'
    if marker not in html:
        raise ValueError(f"Could not locate social metadata marker in {post.slug}")
    return html.replace(marker, marker + metadata, 1)


def post_brand() -> str:
    return '''      <a class="brand" href="../" aria-label="Jiwon Kim Engineering Notes 홈">
        <span class="brand-mark" aria-hidden="true">JK</span>
        <span class="brand-copy"><strong>Jiwon Kim</strong><small>Engineering Notes</small></span>
      </a>'''


def post_navigation() -> str:
    return '''      <nav class="nav-links" aria-label="주요 메뉴">
        <a href="../articles.html">Articles</a>
        <a href="../projects.html">Projects</a>
        <a href="../#about">About</a>
        <span class="nav-divider" aria-hidden="true"></span>
        <a href="https://github.com/andrewkimswe">GitHub</a>
        <a href="https://www.linkedin.com/in/jiwon-kim-867334285/">LinkedIn</a>
      </nav>'''


def post_footer() -> str:
    return '''    <footer class="site-footer">
      <p>© 2026 Jiwon Kim</p>
      <div class="footer-links">
        <span id="visitStatus">집계 중</span>
        <a href="../articles.html">Articles</a>
        <a href="../feed.xml">RSS</a>
      </div>
    </footer>'''


def add_heading_ids(html: str) -> tuple[str, list[tuple[str, str]]]:
    headings: list[tuple[str, str]] = []
    index = 0

    def replacement(match: re.Match[str]) -> str:
        nonlocal index
        index += 1
        attrs = re.sub(r'\s+id="[^"]+"', "", match.group("attrs"))
        content = match.group("content")
        heading_id = f"section-{index:02d}"
        headings.append((heading_id, strip_tags(content)))
        return f'<h2{attrs} id="{heading_id}">{content}</h2>'

    updated = re.sub(
        r'<h2(?P<attrs>[^>]*)>(?P<content>.*?)</h2>',
        replacement,
        html,
        flags=re.S,
    )
    return updated, headings


def render_toc(headings: list[tuple[str, str]]) -> str:
    links = "\n".join(
        f'              <li><a href="#{heading_id}">{escape(label)}</a></li>'
        for heading_id, label in headings
    )
    return f'''        <!-- GENERATED:ARTICLE_TOC:START -->
        <aside class="article-toc" aria-label="이 글의 목차">
          <details open>
            <summary>On this page</summary>
            <ol>
{links}
            </ol>
          </details>
        </aside>
        <!-- GENERATED:ARTICLE_TOC:END -->'''


def related_posts(post: Post, posts: list[Post]) -> list[Post]:
    source_tags = {tag.lower() for tag in post.tags} - GENERIC_RELATED_TAGS

    def score(candidate: Post) -> tuple[int, float]:
        candidate_tags = {tag.lower() for tag in candidate.tags} - GENERIC_RELATED_TAGS
        shared = len(source_tags & candidate_tags)
        topic_bonus = 3 if candidate.topic == post.topic else 0
        distance = abs((candidate.date - post.date).total_seconds())
        return shared * 2 + topic_bonus, -distance

    candidates = [candidate for candidate in posts if candidate.slug != post.slug]
    candidates.sort(key=score, reverse=True)
    return candidates[:3]


def render_adjacent_link(post: Post | None, label: str) -> str:
    if post is None:
        return f'<span class="article-nav-empty"><span>{label}</span><strong>더 이상 글이 없습니다.</strong></span>'
    return (
        f'<a href="./{post.slug}"><span>{label}</span>'
        f'<strong>{escape(post.title)}</strong></a>'
    )


def render_article_tail(post: Post, posts: list[Post], index: int) -> str:
    newer = posts[index - 1] if index > 0 else None
    older = posts[index + 1] if index + 1 < len(posts) else None
    related = related_posts(post, posts)
    related_links = "\n".join(
        f'''          <a href="./{candidate.slug}">
            <span>{escape(candidate.topic)} · {candidate.display_date}</span>
            <strong>{escape(candidate.title)}</strong>
          </a>'''
        for candidate in related
    )
    return f'''        <!-- GENERATED:ARTICLE_TAIL:START -->
        <nav class="article-pagination" aria-label="발행 순서로 읽기">
          {render_adjacent_link(newer, "Newer")}
          {render_adjacent_link(older, "Older")}
        </nav>
        <aside class="related-notes" aria-labelledby="related-heading">
          <h2 id="related-heading">Related notes</h2>
          <div class="related-note-list">
{related_links}
          </div>
        </aside>
        <!-- GENERATED:ARTICLE_TAIL:END -->'''


def remove_generated_block_if_present(html: str, name: str) -> str:
    pattern = re.compile(
        rf'\n?[ \t]*<!-- GENERATED:{re.escape(name)}:START -->.*?'
        rf'^[ \t]*<!-- GENERATED:{re.escape(name)}:END -->\n?',
        re.S | re.M,
    )
    return pattern.sub("\n", html)


def update_post_chrome(post: Post, posts: list[Post], index: int) -> None:
    html = post.path.read_text(encoding="utf-8")
    html = re.sub(
        r'href="\.\./styles\.css(?:\?v=[^"]+)?"',
        f'href="../styles.css?v={ASSET_VERSION}"',
        html,
    )
    html = re.sub(
        r'src="\.\./script\.js(?:\?v=[^"]+)?"',
        f'src="../script.js?v={ASSET_VERSION}"',
        html,
    )
    favicon = '<link rel="icon" href="../assets/favicon.svg" type="image/svg+xml" />'
    if 'rel="icon"' not in html:
        html = html.replace(
            '    <link rel="stylesheet"',
            f'    {favicon}\n    <link rel="stylesheet"',
            1,
        )
    html = re.sub(
        r"<title>.*?</title>",
        f"<title>{escape(post.page_title)} | {TITLE_SUFFIX}</title>",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<meta\s+property="og:site_name"\s+content="[^"]*"\s*/>',
        f'<meta property="og:site_name" content="{SITE_NAME}" />',
        html,
        count=1,
    )
    html = ensure_post_meta(html, post)
    html = re.sub(
        r'("dateModified"\s*:\s*")[^"]+("\s*[,}])',
        lambda match: f'{match.group(1)}{post.modified.isoformat()}{match.group(2)}',
        html,
        count=1,
    )

    if '<a class="skip-link"' not in html:
        html = html.replace(
            "  <body>\n",
            '  <body>\n    <a class="skip-link" href="#main-content">본문으로 바로가기</a>\n',
            1,
        )

    html = re.sub(
        r'      <a class="brand".*?</a>',
        post_brand(),
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'      <nav class="nav-links" aria-label="주요 메뉴">.*?</nav>',
        post_navigation(),
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(r'<main(?:\s+id="main-content")?>', '<main id="main-content">', html, count=1)
    html = html.replace(
        '<a class="back-link" href="../#writing">Back to writing</a>',
        '<a class="back-link" href="../articles.html">All articles</a>',
        1,
    )
    html = html.replace(
        '<a class="back-link" href="../articles.html">← All articles</a>',
        '<a class="back-link" href="../articles.html">All articles</a>',
        1,
    )
    html = re.sub(
        r'    <footer class="site-footer">.*?</footer>',
        post_footer(),
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r'<noscript><img(?![^>]*class=)',
        '<noscript><img class="tracking-pixel"',
        html,
    )

    html = re.sub(
        r'\s*<span class="reading-time" data-generated="true">.*?</span>',
        "",
        html,
        flags=re.S,
    )

    def append_reading_time(match: re.Match[str]) -> str:
        return (
            f'{match.group(1)}{match.group(2)}'
            f'<span class="reading-time" data-generated="true">약 {post.reading_minutes}분</span>'
            f'{match.group(3)}'
        )

    html = re.sub(
        r'(<div class="article-meta">)(.*?)(</div>)',
        append_reading_time,
        html,
        count=1,
        flags=re.S,
    )

    html = remove_generated_block_if_present(html, "ARTICLE_TOC")
    html = remove_generated_block_if_present(html, "ARTICLE_TAIL")
    html = re.sub(
        r'(</header>)[ \t]*(?:\n[ \t]*)+(?=        <div class="article-body">)',
        r'\1\n\n',
        html,
        count=1,
    )
    html, headings = add_heading_ids(html)

    body_marker = '        <div class="article-body">'
    if body_marker not in html:
        raise ValueError(f"Could not locate article body in {post.slug}")
    html = html.replace(body_marker, f"{render_toc(headings)}\n\n{body_marker}", 1)

    html, count = re.subn(
        r'(        </div>)\s*(      </article>)',
        lambda match: (
            f"{match.group(1)}\n\n{render_article_tail(post, posts, index)}\n"
            f"{match.group(2)}"
        ),
        html,
        count=1,
    )
    if count != 1:
        raise ValueError(f"Could not locate article end in {post.slug}")
    post.path.write_text(html, encoding="utf-8")


def update_posts(posts: list[Post]) -> None:
    for index, post in enumerate(posts):
        update_post_chrome(post, posts, index)


def write_feed(posts: list[Post]) -> None:
    latest = max((post.modified for post in posts), default=datetime.now().astimezone())
    items = []
    for post in posts:
        items.append(
            f"""    <item>
      <title>{escape(post.title)}</title>
      <link>{post.url}</link>
      <guid isPermaLink="true">{post.url}</guid>
      <pubDate>{post.rss_date}</pubDate>
      <description>{escape(post.summary)}</description>
    </item>"""
        )
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{SITE_NAME}</title>
    <link>{SITE_URL}/</link>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
    <description>백엔드, 클라우드, RAG, 아키텍처와 운영 판단을 기록하는 기술 블로그입니다.</description>
    <language>ko-KR</language>
    <lastBuildDate>{format_datetime(latest)}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (ROOT / "feed.xml").write_text(feed, encoding="utf-8")


def write_sitemap(posts: list[Post]) -> None:
    latest = max((post.modified for post in posts), default=datetime.now().astimezone()).strftime("%Y-%m-%d")
    pages = (
        (f"{SITE_URL}/", "weekly", "1.0"),
        (f"{SITE_URL}/articles.html", "weekly", "0.9"),
        (f"{SITE_URL}/projects.html", "monthly", "0.8"),
    )
    urls = [
        f"""  <url>
    <loc>{url}</loc>
    <lastmod>{latest}</lastmod>
    <changefreq>{frequency}</changefreq>
    <priority>{priority}</priority>
  </url>"""
        for url, frequency, priority in pages
    ]
    for post in sorted(posts, key=lambda item: (item.date, item.slug)):
        urls.append(
            f"""  <url>
    <loc>{post.url}</loc>
    <lastmod>{post.modified_iso_date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>"""
        )
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def write_llms(posts: list[Post]) -> None:
    lines = [
        f"# {SITE_NAME}",
        "",
        "Jiwon Kim's Korean engineering journal about backend systems, cloud infrastructure, RAG, architecture decisions, and operations.",
        "",
        "## Site",
        "",
        f"- Home: {SITE_URL}/",
        f"- Articles: {SITE_URL}/articles.html",
        f"- Projects: {SITE_URL}/projects.html",
        "- GitHub: https://github.com/andrewkimswe",
        "- LinkedIn: https://www.linkedin.com/in/jiwon-kim-867334285/",
        f"- Sitemap: {SITE_URL}/sitemap.xml",
        f"- RSS: {SITE_URL}/feed.xml",
        "",
        "## Editorial Scope",
        "",
        "- Backend API and data design",
        "- AWS architecture, security, networking, and FinOps",
        "- Kubernetes and operational reliability",
        "- Retrieval-augmented generation evaluation",
        "- Architecture trade-offs and failure analysis",
        "",
        "## Posts",
        "",
    ]
    lines.extend(f"- [{post.title}]({post.url}): {post.description}" for post in posts)
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    posts = load_posts()
    update_listing_pages(posts)
    update_posts(posts)
    write_feed(posts)
    write_sitemap(posts)
    write_llms(posts)
    print(f"Generated site indexes and article navigation for {len(posts)} posts.")


if __name__ == "__main__":
    main()
