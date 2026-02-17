# AI Safety Weekly Digest

A curated weekly digest of AI safety research — papers, technical posts, and reports from leading labs and research organizations. Updated automatically every Monday.

**[Read the latest digest](https://sambhav-mahesh.github.io/ai-safety-digest/)**

## How It Works

Python scripts fetch from 30+ sources, deduplicate, filter for research relevance, enrich missing abstracts, and render a static HTML site deployed to GitHub Pages.

```
config.yaml → fetchers → dedup → research filter → enrich → render → GitHub Pages
```

### Sources

| Type | Sources | Examples |
|------|---------|----------|
| **RSS feeds** | 10 feeds | Anthropic, OpenAI, DeepMind, Alignment Forum, Epoch AI |
| **arXiv** | Keyword search across cs.AI, cs.LG, cs.CL | Safety, alignment, interpretability papers |
| **Web scrapers** | 18 research org sites | METR, Apollo Research, ARC, MIRI, CAIS, UK AISI, GovAI |
| **LessWrong** | GraphQL API (150+ karma) | High-quality technical posts |
| **Trending** | HN + Reddit (research-filtered) | Viral research from r/aisafety, r/mlsafety |

### Pipeline

1. **Fetch** — Each source has a dedicated fetcher returning `Paper` objects
2. **Deduplicate** — Exact title match, then fuzzy matching (>85% similarity)
3. **Filter** — Score-based research relevance filter removes news/opinion
4. **Enrich** — Papers with missing abstracts get them fetched from URLs (arXiv, LessWrong API, meta tags, etc.) or a synthetic fallback
5. **Render** — Jinja2 template + CSS produces a static site with featured hero section, org filters, and expandable abstracts

## Setup

```bash
pip install -r requirements.txt
```

Requires Python 3.9+.

## Usage

```bash
# Fetch papers and render the site
python scripts/fetch.py
python scripts/render.py

# Or do both and open in browser
bash scripts/update-and-open.sh
```

The rendered site is written to `site/index.html`.

## Deployment

A GitHub Actions workflow (`.github/workflows/weekly-update.yml`) runs every Monday at 9 AM UTC:

1. Fetches papers from all sources
2. Renders the site
3. Commits updated `data/papers.json` and `site/index.html`
4. Deploys to GitHub Pages

You can also trigger it manually from the Actions tab.

## Project Structure

```
├── config.yaml              # Source configuration (feeds, scrapers, keywords)
├── scripts/
│   ├── fetch.py             # Main orchestrator — runs the full pipeline
│   ├── render.py            # Jinja2 → static HTML with featured scoring
│   ├── models.py            # Paper dataclass and config loader
│   ├── filter.py            # Research relevance scoring and filtering
│   ├── dedup.py             # Title-based deduplication
│   ├── enrich.py            # Abstract extraction and enrichment
│   └── fetchers/
│       ├── rss.py           # RSS/Atom feeds via feedparser
│       ├── arxiv_fetcher.py # arXiv API
│       ├── scraper.py       # BeautifulSoup web scraper
│       ├── lesswrong.py     # LessWrong GraphQL API
│       └── trending.py      # Hacker News + Reddit
├── templates/
│   └── index.html.j2        # Jinja2 template
├── static/
│   └── style.css            # Stylesheet (inlined at render time)
├── data/
│   └── papers.json          # Fetched paper data (committed)
└── site/
    └── index.html           # Rendered output (deployed to GitHub Pages)
```

## Adding Sources

**RSS feed** — Add an entry to `rss_feeds` in `config.yaml`:
```yaml
- name: "Example Lab"
  url: "https://example.com/feed.xml"
  org: "Example Lab"
  keywords: ["research", "paper", "model"]  # optional, filters entries
```

**Web scraper** — Add an entry to `scrapers` in `config.yaml`:
```yaml
- name: "Example Org"
  url: "https://example.com/research"
  org: "Example Org"
  link_must_contain: "/research/"  # optional, filters link URLs
```

## License

MIT
