import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scout import (ERROR, FOUND, FREE, SITES, UNCLEAR, check_site, classify,
                   scan)


class ClassifyTest(unittest.TestCase):
    def test_200_means_found(self):
        self.assertEqual(classify(200), FOUND)

    def test_404_means_free(self):
        self.assertEqual(classify(404), FREE)

    def test_blocked_status_is_unclear(self):
        self.assertEqual(classify(403), UNCLEAR)
        self.assertEqual(classify(429), UNCLEAR)
        self.assertEqual(classify(500), UNCLEAR)

    def test_unreachable_is_error(self):
        self.assertEqual(classify(-1), ERROR)


class CheckSiteTest(unittest.TestCase):
    SITE = {"name": "Example", "url": "https://example.com/{u}",
            "profile": "https://example.com/{u}"}

    def test_builds_url_with_quoted_username(self):
        def fake_fetch(url, timeout):
            self.assertEqual(url, "https://example.com/my%20name")
            return 200
        record = check_site(self.SITE, "my name", timeout=1, fetch=fake_fetch)
        self.assertEqual(record["result"], FOUND)
        self.assertEqual(record["site"], "Example")

    def test_fetch_exception_becomes_error(self):
        def boom(url, timeout):
            raise OSError("no network")
        record = check_site(self.SITE, "user", timeout=1, fetch=boom)
        self.assertEqual(record["result"], ERROR)
        self.assertEqual(record["status"], -1)


class ScanTest(unittest.TestCase):
    def test_scan_is_offline_testable_and_ordered(self):
        def fake_fetch(url, timeout):
            return 200 if "api.github.com" in url else 404
        results = scan("someone", timeout=1, fetch=fake_fetch)
        self.assertEqual(len(results), len(SITES))
        self.assertEqual(results[0]["site"], "GitHub")
        self.assertEqual(results[0]["result"], FOUND)
        self.assertEqual(results[1]["result"], FREE)


class SiteListTest(unittest.TestCase):
    def test_site_names_are_unique(self):
        names = [site["name"] for site in SITES]
        self.assertEqual(len(names), len(set(names)))

    def test_every_site_has_a_username_placeholder(self):
        for site in SITES:
            self.assertIn("{u}", site["url"])
            self.assertIn("{u}", site["profile"])


if __name__ == "__main__":
    unittest.main()
