# Revue de presse romande

A small automated pipeline that builds a daily French-language news digest for four
Swiss cantons — **Vaud, Genève, Fribourg, Valais** — and publishes it as a live web
page. Built as the Module 3 exercise for the Knight Center course "Advanced Prompt
Engineering for Journalists".

## What it does
1. For each canton, fetches the day's news from Google News (free RSS search, no API key).
2. Applies the editorial rules in `editorial_guidelines.md` (exclude keywords, max items
   per canton, priority sources) and removes duplicates.
3. Writes a dated digest to `digests/revue-AAAA-MM-JJ.md`.
4. Builds a live web page at `web/index.html`.
5. Tracks which articles it has already seen (`data/seen.json`) to know what is new.

## Run it yourself
```bash
python3 digest.py
```
No dependencies to install — it uses the Python standard library only.

## Editorial control (no code needed)
Open `editorial_guidelines.md` and edit the plain-French lists:
- **Réglages**: how many items per canton, the time window.
- **Sources prioritaires**: which outlets to surface first.
- **Exclure (mots-clés)**: any headline containing one of these words is dropped.

When something is misclassified, add a keyword or example here and re-run. The editorial
judgment lives in this file, not in the code.

## How it runs on its own
A GitHub Actions workflow (`.github/workflows/digest.yml`) runs the script every day at
05:00 UTC (07:00 Swiss summer time), commits the new digest, and deploys the web page to
GitHub Pages. You can also trigger it manually from the repository's **Actions** tab.

## Files
- `digest.py` — the pipeline
- `editorial_guidelines.md` — the editorial rules (human-edited)
- `digests/` — one dated digest per day
- `web/index.html` — the published page
- `data/seen.json` — memory of articles already seen
