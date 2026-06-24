#!/usr/bin/env python3
"""
Revue de presse romande — daily news digest pipeline.

What it does, in plain language:
  1. For each canton (Vaud, Geneve, Fribourg, Valais), fetch the day's news from
     Google News (a free RSS search, no API key needed).
  2. Apply the editorial rules from editorial_guidelines.md (exclude keywords,
     max items per canton, priority sources).
  3. Write a dated French digest to digests/revue-AAAA-MM-JJ.md
  4. Build a simple live web page at web/index.html
  5. Remember which articles it has already seen (data/seen.json) so it can tell
     what is new on the next run.

Standard library only. Runs with: python3 digest.py
"""

import json
import re
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GUIDELINES = ROOT / "editorial_guidelines.md"
DIGESTS = ROOT / "digests"
WEB = ROOT / "web"
DATA = ROOT / "data"

CANTONS = ["Vaud", "Genève", "Fribourg", "Valais"]


# ---------- editorial rules ----------

def load_guidelines(path: Path) -> dict:
    """Parse the human-edited editorial_guidelines.md into settings the script uses."""
    cfg = {"max_par_canton": 4, "fenetre_heures": 24,
           "sources_prioritaires": [], "exclure": []}
    if not path.exists():
        return cfg
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        low = s.lower()
        if low.startswith("## réglages") or low.startswith("## reglages"):
            section = "reglages"; continue
        if low.startswith("## sources prioritaires"):
            section = "sources"; continue
        if low.startswith("## exclure"):
            section = "exclure"; continue
        if s.startswith("## "):
            section = None; continue
        if section == "reglages" and s.startswith("-") and ":" in s:
            k, v = s[1:].split(":", 1)
            k, v = k.strip(), v.strip()
            if v.isdigit():
                cfg[k] = int(v)
        elif section == "sources" and s.startswith("-"):
            cfg["sources_prioritaires"].append(s[1:].strip())
        elif section == "exclure" and s.startswith("-"):
            cfg["exclure"].append(s[1:].strip().lower())
    return cfg


# ---------- fetching ----------

def fetch_canton(canton: str, hours: int) -> list:
    """Fetch recent Google News items for one canton, in French, Swiss edition."""
    query = urllib.parse.quote(f"{canton} when:{max(1, hours // 24)}d")
    url = (f"https://news.google.com/rss/search?q={query}"
           f"&hl=fr&gl=CH&ceid=CH:fr")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=25).read()
    root = ET.fromstring(raw)
    items = []
    for it in root.findall(".//item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub = (it.findtext("pubDate") or "").strip()
        src_el = it.find("{*}source")
        source = src_el.text.strip() if src_el is not None and src_el.text else ""
        # Google formats titles as "Headline - Source"; drop the trailing source.
        clean = re.sub(r"\s*-\s*[^-]+$", "", title) if source and title.endswith(source) else title
        items.append({"canton": canton, "title": clean.strip(),
                      "raw_title": title, "link": link, "source": source, "pub": pub})
    return items


# ---------- curating ----------

def excluded(title: str, exclude_kw: list) -> bool:
    low = title.lower()
    return any(kw and kw in low for kw in exclude_kw)


def _words(title: str) -> set:
    t = re.sub(r"[^a-zàâçéèêëîïôûùüÿñæœ0-9 ]", " ", title.lower())
    return {w for w in t.split() if len(w) > 2}


def dedupe(items: list) -> list:
    """Drop near-duplicate stories (same event, different wording) by word overlap."""
    out, kept = [], []
    for it in items:
        ws = _words(it["title"])
        if not ws:
            continue
        if any((len(ws & k) / len(ws | k)) >= 0.5 for k in kept if (ws | k)):
            continue
        kept.append(ws)
        out.append(it)
    return out


def is_junk(title: str) -> bool:
    """Skip non-articles like 'Play RTS' or bare labels: too few real words."""
    return len(_words(title)) < 4


def curate(items: list, cfg: dict) -> list:
    items = [it for it in items if it["title"]
             and not excluded(it["title"], cfg["exclure"])
             and not is_junk(it["title"])]
    items = dedupe(items)
    prio = [s.lower() for s in cfg["sources_prioritaires"]]

    def rank(it):
        src = it["source"].lower()
        pos = next((i for i, p in enumerate(prio) if p and p in src), len(prio))
        return pos
    items.sort(key=rank)
    return items[:cfg["max_par_canton"]]


# ---------- rendering ----------

def render_markdown(date_str: str, by_canton: dict) -> str:
    lines = [f"# Revue de presse romande — {date_str}", ""]
    for canton in CANTONS:
        items = by_canton.get(canton, [])
        lines.append(f"## {canton}")
        if not items:
            lines.append("_Pas d'actualité retenue aujourd'hui._\n")
            continue
        for it in items:
            src = f" — {it['source']}" if it["source"] else ""
            lines.append(f"- [{it['title']}]({it['link']}){src}")
        lines.append("")
    lines.append("---")
    lines.append(f"_Généré automatiquement le {date_str}. Sources : Google News (édition CH-fr)._")
    return "\n".join(lines)


def render_html(date_str: str, by_canton: dict) -> str:
    cards = []
    for canton in CANTONS:
        items = by_canton.get(canton, [])
        rows = ""
        if not items:
            rows = '<p class="empty">Pas d\'actualité retenue aujourd\'hui.</p>'
        else:
            for it in items:
                src = html.escape(it["source"])
                title = html.escape(it["title"])
                link = html.escape(it["link"])
                rows += (f'<li><a href="{link}" target="_blank" rel="noopener">{title}</a>'
                         f'<span class="src">{src}</span></li>')
        cards.append(f'<section class="canton"><h2>{canton}</h2><ul>{rows}</ul></section>')
    body = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revue de presse romande — {date_str}</title>
<style>
  :root {{ --ink:#1a1a1a; --muted:#6b7280; --line:#e5e7eb; --accent:#b4232a; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
         color:var(--ink); max-width:820px; margin:0 auto; padding:2.5rem 1.25rem;
         line-height:1.5; }}
  header {{ border-bottom:3px solid var(--accent); padding-bottom:1rem; margin-bottom:1.5rem; }}
  h1 {{ font-size:1.7rem; margin:0; }}
  .date {{ color:var(--muted); margin-top:.25rem; }}
  .canton {{ margin:1.75rem 0; }}
  .canton h2 {{ font-size:1.15rem; margin:0 0 .6rem; padding-bottom:.3rem;
               border-bottom:1px solid var(--line); }}
  ul {{ list-style:none; padding:0; margin:0; }}
  li {{ padding:.5rem 0; border-bottom:1px solid var(--line); }}
  li a {{ color:var(--ink); text-decoration:none; font-weight:500; }}
  li a:hover {{ color:var(--accent); text-decoration:underline; }}
  .src {{ display:block; color:var(--muted); font-size:.82rem; margin-top:.15rem; }}
  .empty {{ color:var(--muted); font-style:italic; }}
  footer {{ margin-top:2.5rem; color:var(--muted); font-size:.82rem;
           border-top:1px solid var(--line); padding-top:1rem; }}
</style>
</head>
<body>
<header>
  <h1>Revue de presse romande</h1>
  <div class="date">{date_str} · Vaud · Genève · Fribourg · Valais</div>
</header>
{body}
<footer>Généré automatiquement. Sources : Google News (édition CH-fr).
Règles éditoriales : editorial_guidelines.md.</footer>
</body>
</html>"""


# ---------- new-since-last-run tracking ----------

def update_seen(all_items: list) -> int:
    DATA.mkdir(exist_ok=True)
    seen_file = DATA / "seen.json"
    seen = set(json.loads(seen_file.read_text()) if seen_file.exists() else [])
    new = [it for it in all_items if it["link"] not in seen]
    seen.update(it["link"] for it in all_items)
    seen_file.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=0))
    return len(new)


# ---------- main ----------

def main():
    cfg = load_guidelines(GUIDELINES)
    date_str = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    by_canton, all_items = {}, []
    for canton in CANTONS:
        try:
            raw = fetch_canton(canton, cfg["fenetre_heures"])
        except Exception as e:
            print(f"[!] {canton}: fetch failed ({e})")
            raw = []
        kept = curate(raw, cfg)
        by_canton[canton] = kept
        all_items.extend(kept)
        print(f"[ok] {canton}: {len(raw)} trouvés, {len(kept)} retenus")

    DIGESTS.mkdir(exist_ok=True)
    WEB.mkdir(exist_ok=True)
    (DIGESTS / f"revue-{date_str}.md").write_text(render_markdown(date_str, by_canton), encoding="utf-8")
    (WEB / "index.html").write_text(render_html(date_str, by_canton), encoding="utf-8")
    n_new = update_seen(all_items)

    print(f"\nDigest écrit : digests/revue-{date_str}.md")
    print(f"Page web     : web/index.html")
    print(f"Nouveaux articles depuis le dernier passage : {n_new}")


if __name__ == "__main__":
    main()
