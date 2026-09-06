from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.publish_scheduled import inspect_scheduled, publish_due


class PublishScheduledTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "scheduled").mkdir()
        (self.root / "posts").mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_post(
        self,
        name: str,
        published: str,
        *,
        canonical_name: str | None = None,
        visible_date: str | None = None,
    ) -> Path:
        canonical_name = canonical_name or name
        visible_date = visible_date or published[:10]
        url = f"https://andrewkimswe.github.io/posts/{canonical_name}"
        path = self.root / "scheduled" / name
        path.write_text(
            f'''<!doctype html>
<html lang="ko">
  <head>
    <meta name="description" content="Scheduled post test" />
    <link rel="canonical" href="{url}" />
    <meta property="og:title" content="Scheduled post" />
    <meta property="og:description" content="Scheduled post test" />
    <meta property="og:url" content="{url}" />
    <meta property="article:published_time" content="{published}" />
    <meta property="article:modified_time" content="{published}" />
    <meta property="article:tag" content="Test" />
    <script type="application/ld+json">{{"datePublished":"{published}","dateModified":"{published}"}}</script>
  </head>
  <body>
    <h1>Scheduled post</h1>
    <time datetime="{visible_date}">{visible_date}</time>
    <div class="article-body"><h2>Section</h2></div>
  </body>
</html>
''',
            encoding="utf-8",
        )
        return path

    def test_publishes_only_due_posts(self) -> None:
        due = self.write_post("due.html", "2026-09-07T09:00:00+09:00")
        future = self.write_post("future.html", "2026-09-08T09:00:00+09:00")

        published = publish_due(
            self.root,
            datetime.fromisoformat("2026-09-07T09:00:00+09:00"),
        )

        self.assertEqual([post.source.name for post in published], ["due.html"])
        self.assertFalse(due.exists())
        self.assertTrue((self.root / "posts" / "due.html").exists())
        self.assertTrue(future.exists())

    def test_dry_run_does_not_move_due_post(self) -> None:
        due = self.write_post("due.html", "2026-09-07T09:00:00+09:00")

        published = publish_due(
            self.root,
            datetime.fromisoformat("2026-09-07T09:00:00+09:00"),
            dry_run=True,
        )

        self.assertEqual(len(published), 1)
        self.assertTrue(due.exists())
        self.assertFalse((self.root / "posts" / "due.html").exists())

    def test_rejects_timestamp_without_timezone(self) -> None:
        self.write_post("invalid.html", "2026-09-07T09:00:00")

        with self.assertRaisesRegex(ValueError, "timezone offset"):
            inspect_scheduled(
                self.root,
                datetime.fromisoformat("2026-09-07T09:00:00+09:00"),
            )

    def test_rejects_mismatched_public_url(self) -> None:
        self.write_post(
            "scheduled.html",
            "2026-09-07T09:00:00+09:00",
            canonical_name="another.html",
        )

        with self.assertRaisesRegex(ValueError, "final post URL"):
            inspect_scheduled(
                self.root,
                datetime.fromisoformat("2026-09-07T09:00:00+09:00"),
            )

    def test_collision_blocks_every_move(self) -> None:
        first = self.write_post("first.html", "2026-09-07T08:00:00+09:00")
        second = self.write_post("second.html", "2026-09-07T08:00:00+09:00")
        (self.root / "posts" / "second.html").write_text("existing", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "destination already exists"):
            publish_due(
                self.root,
                datetime.fromisoformat("2026-09-07T09:00:00+09:00"),
            )

        self.assertTrue(first.exists())
        self.assertTrue(second.exists())
        self.assertFalse((self.root / "posts" / "first.html").exists())

    def test_rejects_visible_date_drift(self) -> None:
        self.write_post(
            "drift.html",
            "2026-09-07T09:00:00+09:00",
            visible_date="2026-09-08",
        )

        with self.assertRaisesRegex(ValueError, "visible date"):
            inspect_scheduled(
                self.root,
                datetime.fromisoformat("2026-09-07T09:00:00+09:00"),
            )

    def test_rejects_incomplete_article_structure(self) -> None:
        path = self.write_post("incomplete.html", "2026-09-07T09:00:00+09:00")
        path.write_text(
            path.read_text(encoding="utf-8").replace("<h1>Scheduled post</h1>", ""),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "exactly one h1"):
            inspect_scheduled(
                self.root,
                datetime.fromisoformat("2026-09-07T09:00:00+09:00"),
            )


if __name__ == "__main__":
    unittest.main()
