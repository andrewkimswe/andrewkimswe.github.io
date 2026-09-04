#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.utils import format_datetime
from html import escape, unescape
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://andrewkimswe.github.io"
SITE_NAME = "Jiwon Kim's Blog"
SOCIAL_IMAGE = f"{SITE_URL}/assets/social-card.svg"


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

    @property
    def modified_rss_date(self) -> str:
        return format_datetime(self.modified)


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
        data_tags=" ".join(sorted(data_terms, key=str.lower)),
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
        key=lambda p: (p.date, p.slug),
        reverse=True,
    )


def render_post_rows(posts: list[Post]) -> str:
    rows = []
    for post in posts:
        rows.append(
            f'''          <article
            class="post-row"
            data-tags="{escape(post.data_tags, quote=True)}"
            data-title="{escape(post.title, quote=True)}"
          >
            <a href="./posts/{post.slug}">
              <time datetime="{post.iso_date}">{post.display_date}</time>
              <span class="post-topic">{escape(post.topic)}</span>
              <h3>{escape(post.title)}</h3>
              <p>{escape(post.summary)}</p>
            </a>
          </article>'''
        )
    return "\n".join(rows)


def update_index(posts: list[Post]) -> None:
    path = ROOT / "index.html"
    html = path.read_text(encoding="utf-8")
    html = ensure_social_meta(html, is_home=True)
    replacement = r'\1' + render_post_rows(posts).replace("\\", r"\\") + r'\3'
    html = re.sub(
        r'(<div class="post-list" id="postGrid"[^>]*>\n)(.*?)(\n        </div>\n      </section>\n\n      <section class="section portfolio-section")',
        replacement,
        html,
        flags=re.S,
    )
    path.write_text(html, encoding="utf-8")


def ensure_social_meta(html: str, is_home: bool = False) -> str:
    image_meta = (
        f'    <meta property="og:image" content="{SOCIAL_IMAGE}" />\n'
        f'    <meta name="twitter:card" content="summary_large_image" />\n'
        f'    <meta name="twitter:image" content="{SOCIAL_IMAGE}" />'
    )
    html = re.sub(r'\n\s*<meta property="og:image" content="[^"]+" />', "", html)
    html = re.sub(r'\n\s*<meta name="twitter:image" content="[^"]+" />', "", html)
    html = re.sub(r'\n\s*<meta name="twitter:card" content="[^"]+" />', "", html)
    if 'meta property="og:image"' not in html:
        html = re.sub(
            r'((?:    <meta\s+property="og:url"\s+content="[^"]+"\s+/>)|(?:    <meta\s*\n\s+property="og:url"\s*\n\s+content="[^"]+"\s*\n\s*/>))',
            r"\1\n" + image_meta,
            html,
            count=1,
        )
    return html


def update_posts_social_meta(posts: list[Post]) -> None:
    for post in posts:
        html = post.path.read_text(encoding="utf-8")
        post.path.write_text(ensure_social_meta(html), encoding="utf-8")


def write_feed(posts: list[Post]) -> None:
    latest = max((post.modified for post in posts), default=datetime.now().astimezone())
    items = []
    for post in posts:
        items.append(
            f"""    <item>
      <title>{escape(post.title)}</title>
      <link>{post.url}</link>
      <guid>{post.url}</guid>
      <pubDate>{post.rss_date}</pubDate>
      <description>{escape(post.summary)}</description>
    </item>"""
        )
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{SITE_NAME}</title>
    <link>{SITE_URL}/</link>
    <description>백엔드, 클라우드, 아키텍처, 운영, 트러블슈팅을 기록하는 기술 블로그입니다.</description>
    <language>ko-KR</language>
    <lastBuildDate>{format_datetime(latest)}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (ROOT / "feed.xml").write_text(feed, encoding="utf-8")


def write_sitemap(posts: list[Post]) -> None:
    latest = max((post.modified for post in posts), default=datetime.now().astimezone()).strftime("%Y-%m-%d")
    urls = [
        f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{latest}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>"""
    ]
    for post in sorted(posts, key=lambda p: p.date):
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
        "Jiwon Kim's Blog is a Korean technical blog about backend engineering, cloud infrastructure, architecture, operations, and troubleshooting.",
        "",
        "## Site",
        "",
        f"- Home: {SITE_URL}/",
        "- GitHub: https://github.com/andrewkimswe",
        "- LinkedIn: https://www.linkedin.com/in/jiwon-kim-867334285/",
        f"- Sitemap: {SITE_URL}/sitemap.xml",
        f"- RSS: {SITE_URL}/feed.xml",
        "",
        "## Main Topics",
        "",
        "- Backend API design",
        "- Cloud architecture",
        "- LLM application architecture",
        "- Retrieval-augmented generation evaluation",
        "- AWS FinOps and cost analytics",
        "- AWS deployment and operations",
        "- Incident reviews",
        "- Engineering documentation",
        "",
        "## Posts",
        "",
    ]
    lines.extend(f"- [{post.title}]({post.url}): {post.description}" for post in posts)
    (ROOT / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    posts = load_posts()
    update_posts_social_meta(posts)
    update_index(posts)
    write_feed(posts)
    write_sitemap(posts)
    write_llms(posts)
    print(f"Generated site indexes for {len(posts)} posts.")


if __name__ == "__main__":
    main()
