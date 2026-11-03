"""Tests for ai_overviews_tracker.py. Run with: python3 -m unittest discover tests"""

import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_overviews_tracker import (
    CHECKS_CSV,
    KEYWORDS_CSV,
    log_check,
    read_checks,
    read_keywords,
    summarise,
)


class TrackerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        with (self.tmp / KEYWORDS_CSV).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["keyword", "date_added"])
            writer.writerow(["best plumber near me", "2026-11-03"])
            writer.writerow(["how to fix a leaking tap", "2026-11-03"])
            writer.writerow(["emergency drain cleaning", "2026-11-03"])

    def test_read_keywords(self):
        self.assertEqual(
            read_keywords(self.tmp / KEYWORDS_CSV),
            ["best plumber near me", "how to fix a leaking tap", "emergency drain cleaning"],
        )

    def test_log_and_read_checks(self):
        log_check(self.tmp / CHECKS_CSV, "best plumber near me", True, notes="long answer box")
        log_check(self.tmp / CHECKS_CSV, "how to fix a leaking tap", False)
        rows = read_checks(self.tmp / CHECKS_CSV)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["keyword"], "best plumber near me")
        self.assertEqual(rows[0]["has_ai_overview"], "yes")
        self.assertEqual(rows[1]["has_ai_overview"], "no")

    def test_summarise_latest_wins(self):
        log_check(self.tmp / CHECKS_CSV, "best plumber near me", False, check_date="2026-10-01")
        log_check(self.tmp / CHECKS_CSV, "best plumber near me", True, check_date="2026-11-03")
        log_check(self.tmp / CHECKS_CSV, "how to fix a leaking tap", False)
        summary = summarise(read_keywords(self.tmp / KEYWORDS_CSV), read_checks(self.tmp / CHECKS_CSV))
        self.assertEqual(summary["total_keywords"], 3)
        self.assertEqual(summary["checked"], 2)
        self.assertEqual(summary["triggering"], ["best plumber near me"])
        self.assertEqual(summary["not_triggering"], ["how to fix a leaking tap"])
        self.assertEqual(summary["unlogged"], ["emergency drain cleaning"])
        self.assertEqual(summary["trigger_rate_pct"], 50.0)

    def test_summarise_empty_log(self):
        summary = summarise(read_keywords(self.tmp / KEYWORDS_CSV), [])
        self.assertEqual(summary["checked"], 0)
        self.assertEqual(summary["trigger_rate_pct"], 0.0)
        self.assertEqual(len(summary["unlogged"]), 3)

    def test_bad_keywords_header(self):
        with (self.tmp / "bad.csv").open("w", encoding="utf-8") as fh:
            fh.write("wrong,header\n")
        with self.assertRaises(SystemExit):
            read_keywords(self.tmp / "bad.csv")


if __name__ == "__main__":
    unittest.main()
