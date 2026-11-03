#!/usr/bin/env python3
"""AI Overviews Tracker.

A small, honest toolkit for tracking which of your target keywords trigger
a Google AI Overview.

Google offers no free API for detecting AI Overviews, so this tool follows
a manual-check workflow:
  1. Keep your keyword list in keywords.csv (one keyword per row).
  2. Check each keyword in Google (an incognito window works best),
     and log whether an AI Overview appeared.
  3. Run `report` to aggregate the CSV log into a summary.

Everything is stdlib Python: no installs, no API keys, no scraping.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from datetime import date
from pathlib import Path

KEYWORDS_CSV = "keywords.csv"
CHECKS_CSV = "checks.csv"

KEYWORDS_HEADER = ["keyword", "date_added"]
CHECKS_HEADER = ["date", "keyword", "has_ai_overview", "notes"]


def _ensure_file(path: Path, header: list[str]) -> None:
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(header)


def init_keywords(keywords_file: Path) -> int:
    """Create a keywords.csv template if none exists. Returns 0."""
    if keywords_file.exists():
        print(f"{keywords_file} already exists, leaving it untouched.")
        return 0
    with keywords_file.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(KEYWORDS_HEADER)
        writer.writerow(["best plumber near me", str(date.today())])
        writer.writerow(["how to fix a leaking tap", str(date.today())])
    print(f"Created {keywords_file} with example rows. Edit it to add your keywords.")
    return 0


def read_keywords(keywords_file: Path) -> list[str]:
    """Return the keyword list (first column), skipping blanks and header."""
    if not keywords_file.exists():
        raise SystemExit(f"Missing {keywords_file}. Run the init command first.")
    keywords: list[str] = []
    with keywords_file.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != KEYWORDS_HEADER:
            raise SystemExit(
                f"Unexpected header in {keywords_file}: {reader.fieldnames}. "
                f"Expected {KEYWORDS_HEADER}."
            )
        for row in reader:
            kw = (row.get("keyword") or "").strip()
            if kw:
                keywords.append(kw)
    return keywords


def log_check(
    checks_file: Path,
    keyword: str,
    has_overview: bool,
    notes: str = "",
    check_date: str | None = None,
) -> None:
    """Append one manual check row to checks.csv."""
    _ensure_file(checks_file, CHECKS_HEADER)
    with checks_file.open("a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow(
            [check_date or str(date.today()), keyword, "yes" if has_overview else "no", notes]
        )


def read_checks(checks_file: Path) -> list[dict[str, str]]:
    if not checks_file.exists():
        return []
    with checks_file.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != CHECKS_HEADER:
            raise SystemExit(
                f"Unexpected header in {checks_file}: {reader.fieldnames}. "
                f"Expected {CHECKS_HEADER}."
            )
        return [row for row in reader]


def summarise(keywords: list[str], checks: list[dict[str, str]]) -> dict:
    """Aggregate the log into a summary dict. Latest check per keyword wins."""
    latest: dict[str, dict[str, str]] = {}
    for row in checks:
        latest[row["keyword"]] = row
    checked = {kw: latest[kw] for kw in keywords if kw in latest}
    triggering = sorted(kw for kw, row in checked.items() if row["has_ai_overview"] == "yes")
    not_triggering = sorted(kw for kw, row in checked.items() if row["has_ai_overview"] != "yes")
    unlogged = sorted(kw for kw in keywords if kw not in latest)
    return {
        "total_keywords": len(keywords),
        "checked": len(checked),
        "triggering": triggering,
        "not_triggering": not_triggering,
        "unlogged": unlogged,
        "trigger_rate_pct": round(100 * len(triggering) / len(checked), 1) if checked else 0.0,
    }


def print_report(summary: dict) -> None:
    print(f"Keywords tracked : {summary['total_keywords']}")
    print(f"Keywords checked : {summary['checked']}")
    print(f"AI Overview rate : {summary['trigger_rate_pct']}%")
    print()
    print(f"Triggering an AI Overview ({len(summary['triggering'])}):")
    for kw in summary["triggering"]:
        print(f"  - {kw}")
    print()
    print(f"NOT triggering ({len(summary['not_triggering'])}):")
    for kw in summary["not_triggering"]:
        print(f"  - {kw}")
    if summary["unlogged"]:
        print()
        print(f"Not yet checked ({len(summary['unlogged'])}):")
        for kw in summary["unlogged"]:
            print(f"  - {kw}")


def cmd_init(args: argparse.Namespace) -> int:
    return init_keywords(Path(args.dir) / KEYWORDS_CSV)


def cmd_list(args: argparse.Namespace) -> int:
    for kw in read_keywords(Path(args.dir) / KEYWORDS_CSV):
        print(kw)
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    if args.keyword is None:
        args.parser.error("--keyword is required for the log command")
    log_check(
        Path(args.dir) / CHECKS_CSV,
        args.keyword,
        args.result == "yes",
        notes=args.notes or "",
        check_date=args.date,
    )
    print(f"Logged: {args.keyword} -> {args.result}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    base = Path(args.dir)
    keywords = read_keywords(base / KEYWORDS_CSV)
    checks = read_checks(base / CHECKS_CSV)
    print_report(summarise(keywords, checks))
    if args.csv_out:
        summary = summarise(keywords, checks)
        out = Path(args.csv_out)
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["keyword", "has_ai_overview"])
            for kw in summary["triggering"]:
                writer.writerow([kw, "yes"])
            for kw in summary["not_triggering"]:
                writer.writerow([kw, "no"])
        print(f"\nWrote {out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai_overviews_tracker",
        description="Track which of your keywords trigger a Google AI Overview.",
    )
    parser.add_argument(
        "--dir",
        default=".",
        help="Directory holding keywords.csv and checks.csv (default: current dir).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create a keywords.csv template.")
    p_init.set_defaults(func=cmd_init)

    p_list = sub.add_parser("list", help="List tracked keywords.")
    p_list.set_defaults(func=cmd_list)

    p_log = sub.add_parser("log", help="Log one manual check for a keyword.")
    p_log.add_argument("--keyword", required=True, help="The keyword you checked.")
    p_log.add_argument(
        "--result",
        choices=["yes", "no"],
        default="yes",
        help="Whether an AI Overview appeared: yes or no (default: yes).",
    )
    p_log.add_argument("--notes", default="", help="Optional note about the result.")
    p_log.add_argument(
        "--date",
        default=None,
        help="Check date as YYYY-MM-DD (default: today).",
    )
    p_log.set_defaults(func=cmd_log)

    p_report = sub.add_parser("report", help="Print a summary of the log.")
    p_report.add_argument(
        "--csv-out",
        default=None,
        help="Also write a per-keyword result CSV to this path.",
    )
    p_report.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.parser = parser
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
