#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://andrewkimswe.github.io"


@dataclass(frozen=True)
class ScheduledPost:
    source: Path
    destination: Path
    publish_at: datetime


def extract_required(pattern: str, html: str, label: str, path: Path) -> str:
    match = re.search(pattern, html, re.S)
    if not match:
        raise ValueError(f"{path}: missing {label}")
    return match.group(1).strip()


def parse_timestamp(raw: str, label: str, path: Path) -> datetime:
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        value = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{path}: invalid {label}: {raw}") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{path}: {label} must include a timezone offset")
    return value


def inspect_post(path: Path, posts_dir: Path) -> ScheduledPost:
    html = path.read_text(encoding="utf-8")
    for label, pattern in (
        ("description", r'<meta\s+name="description"\s+content="([^"]+)"\s*/>'),
        ("og:title", r'<meta\s+property="og:title"\s+content="([^"]+)"\s*/>'),
        ("og:description", r'<meta\s+property="og:description"\s+content="([^"]+)"\s*/>'),
        ("article:tag", r'<meta\s+property="article:tag"\s+content="([^"]+)"\s*/>'),
    ):
        extract_required(pattern, html, label, path)

    if len(re.findall(r"<h1(?:\s|>)", html)) != 1:
        raise ValueError(f"{path}: scheduled post must contain exactly one h1")
    if '<div class="article-body">' not in html or not re.search(r"<h2(?:\s|>)", html):
        raise ValueError(f"{path}: scheduled post must contain an article body and h2")

    published_raw = extract_required(
        r'<meta\s+property="article:published_time"\s+content="([^"]+)"\s*/>',
        html,
        "article:published_time",
        path,
    )
    publish_at = parse_timestamp(published_raw, "article:published_time", path)

    json_published = extract_required(
        r'"datePublished"\s*:\s*"([^"]+)"',
        html,
        "JSON-LD datePublished",
        path,
    )
    if parse_timestamp(json_published, "JSON-LD datePublished", path) != publish_at:
        raise ValueError(f"{path}: JSON-LD datePublished differs from article:published_time")

    modified_raw = extract_required(
        r'<meta\s+property="article:modified_time"\s+content="([^"]+)"\s*/>',
        html,
        "article:modified_time",
        path,
    )
    modified_at = parse_timestamp(modified_raw, "article:modified_time", path)
    json_modified = extract_required(
        r'"dateModified"\s*:\s*"([^"]+)"',
        html,
        "JSON-LD dateModified",
        path,
    )
    if parse_timestamp(json_modified, "JSON-LD dateModified", path) != modified_at:
        raise ValueError(f"{path}: JSON-LD dateModified differs from article:modified_time")

    canonical = extract_required(
        r'<link\s+rel="canonical"\s+href="([^"]+)"\s*/>',
        html,
        "canonical URL",
        path,
    )
    og_url = extract_required(
        r'<meta\s+property="og:url"\s+content="([^"]+)"\s*/>',
        html,
        "og:url",
        path,
    )
    expected_url = f"{SITE_URL}/posts/{path.name}"
    if canonical != expected_url or og_url != expected_url:
        raise ValueError(
            f"{path}: canonical and og:url must both be the final post URL {expected_url}"
        )

    visible_date = extract_required(
        r'<time\s+datetime="([^"]+)"',
        html,
        "visible article date",
        path,
    )
    if visible_date != publish_at.date().isoformat():
        raise ValueError(
            f"{path}: visible date {visible_date} differs from scheduled date "
            f"{publish_at.date().isoformat()}"
        )

    destination = posts_dir / path.name
    if destination.exists():
        raise ValueError(f"{path}: destination already exists: {destination}")
    return ScheduledPost(path, destination, publish_at)


def inspect_scheduled(root: Path, now: datetime) -> tuple[list[ScheduledPost], list[ScheduledPost]]:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("current time must include a timezone offset")

    scheduled_dir = root / "scheduled"
    posts_dir = root / "posts"
    scheduled_dir.mkdir(parents=True, exist_ok=True)
    posts_dir.mkdir(parents=True, exist_ok=True)

    inspected: list[ScheduledPost] = []
    errors: list[str] = []
    for path in sorted(scheduled_dir.glob("*.html")):
        try:
            inspected.append(inspect_post(path, posts_dir))
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(str(exc))

    if errors:
        raise ValueError("Scheduled post validation failed:\n- " + "\n- ".join(errors))

    inspected.sort(key=lambda post: (post.publish_at, post.source.name))
    now_utc = now.astimezone(timezone.utc)
    due = [post for post in inspected if post.publish_at.astimezone(timezone.utc) <= now_utc]
    return inspected, due


def publish_due(root: Path, now: datetime, dry_run: bool = False) -> list[ScheduledPost]:
    _, due = inspect_scheduled(root, now)
    if dry_run:
        return due

    for post in due:
        post.source.replace(post.destination)
    return due


def parse_now(raw: str | None) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)
    return parse_timestamp(raw, "--now", Path("<command line>"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and publish due HTML posts from scheduled/ to posts/."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--now",
        help="Override the current time with an ISO-8601 value including an offset.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Validate every scheduled post without moving files.",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="List posts due at --now without moving files.",
    )
    args = parser.parse_args()

    try:
        now = parse_now(args.now)
        if args.check:
            inspected, _ = inspect_scheduled(args.root.resolve(), now)
            print(f"Scheduled post validation passed for {len(inspected)} post(s).")
            return 0

        due = publish_due(args.root.resolve(), now, dry_run=args.dry_run)
    except (OSError, UnicodeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    if not due:
        print("No scheduled posts are due.")
        return 0

    action = "Would publish" if args.dry_run else "Published"
    names = ", ".join(post.source.name for post in due)
    print(f"{action} {len(due)} scheduled post(s): {names}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
