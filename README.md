# AI Overviews Tracker

A small Python toolkit for tracking which of your target keywords trigger a
Google **AI Overview** (the AI-generated answer box at the top of Google
search results).

## Why manual checks?

Google offers **no free API** that tells you whether an AI Overview appears
for a keyword. Any tool claiming fully automatic detection is either scraping
Google (fragile, and against its terms) or selling you an API subscription.
This tracker takes the honest route: a fast manual-check workflow with a CSV
log, and a script that turns the log into a summary you can act on.

## Quick start

Requires Python 3.8+. No dependencies (stdlib only), so no `pip install` is
needed. `requirements.txt` is present and intentionally empty.

```bash
# 1. Create your keyword list template (edit keywords.csv afterwards)
python3 ai_overviews_tracker.py init

# 2. Log each manual check (use an incognito window for cleaner results)
python3 ai_overviews_tracker.py log --keyword "best plumber near me" --result yes
python3 ai_overviews_tracker.py log --keyword "how to fix a leaking tap" --result no

# 3. See the summary
python3 ai_overviews_tracker.py report
```

## Workflow

1. Put one keyword per row in `keywords.csv` (`keyword,date_added`).
2. Google each keyword and note whether an AI Overview appeared.
   Tips for consistent results:
   - Use an incognito window so personalization does not skew results.
   - Results vary by location and date, so always log the date
     (`--date YYYY-MM-DD`).
   - Re-check monthly: AI Overview coverage changes fast.
3. Run `report` to aggregate everything.

## Commands

| Command | What it does |
|---|---|
| `init` | Create `keywords.csv` with example rows |
| `list` | Print all tracked keywords |
| `log --keyword "..." [--result yes\|no] [--notes "..."] [--date YYYY-MM-DD]` | Record one manual check in `checks.csv` |
| `report [--csv-out file.csv]` | Print a summary; optionally export per-keyword results |

## Example report

```
Keywords tracked : 3
Keywords checked : 2
AI Overview rate : 50.0%

Triggering an AI Overview (1):
  - best plumber near me

NOT triggering (1):
  - how to fix a leaking tap

Not yet checked (1):
  - emergency drain cleaning
```

Re-check a keyword later and `report` flags any keyword whose AI Overview
status flipped since its previous check, under
"Changed since previous check". That is the signal that matters most: a
keyword gaining an AI Overview pushes your organic result down the page, and
a keyword losing one opens a window to win clicks back.

## What this tells you (SEO use)

Keywords with an AI Overview push organic results further down the page and
are harder to win clicks from. Common plays:

- Target the **non-triggering** keywords first for quicker organic wins.
- For triggering keywords, aim to be *cited inside* the AI Overview with
  concise, factual, well-structured content (definitions, steps, FAQs).
- Track the trigger rate over time to see how Google's coverage expands.

## Files

- `ai_overviews_tracker.py` - the CLI (init, list, log, report)
- `tests/test_tracker.py` - unit tests (`python3 -m unittest discover tests`)
- `keywords.csv` - your keyword list (created by `init`, edit freely)
- `checks.csv` - the manual-check log (created by the first `log` call)
- `requirements.txt` - empty on purpose; the project uses stdlib only

## License

MIT. See `LICENSE`.
