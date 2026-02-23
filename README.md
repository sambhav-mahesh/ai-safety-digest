# AI Safety Weekly Digest

A curated weekly digest of AI safety research — papers, technical posts, and reports from leading labs and research organizations.

**[Read the latest digest](https://sambhav-mahesh.github.io/ai-safety-digest/)**

## Reading the Digest

No setup required. Just bookmark the link above. The digest updates automatically every Monday with the latest AI safety research from the past week.

You can also open `site/index.html` directly in any browser if you clone the repo.

## Sources

The digest aggregates research from 45+ sources across six fetcher types:

### RSS Feeds
| Organization | Feed |
|---|---|
| Google DeepMind | Blog RSS (safety keywords filtered) |
| Microsoft Research | Research feed (AI keyword filtered) |
| Anthropic | News + Engineering (via community RSS mirrors) |
| OpenAI | News RSS (Research/Safety/Publication categories) + Alignment Research Blog |
| Redwood Research | Blog RSS |
| Alignment Forum | Feed (research keyword filtered) |
| Dean Ball | Hyperdimensional Substack (all posts) |
| Seb Krier | Technologik Substack (all posts) |
| Peter Wildeford | The Power Law Substack (all posts) |
| Ajeya Cotra | Planned Obsolescence (all posts) |
| Dan Hendrycks | ML Safety Newsletter |
| FLI | Blog feed |
| Epoch AI | Blog RSS |
| METR | Blog RSS feed |
| Zvi Mowshowitz | Substack feed (AI/safety keyword filtered) |
| SemiAnalysis | Newsletter feed (AI/compute keyword filtered) |

### arXiv
Keyword search across `cs.AI`, `cs.LG`, `cs.CL` for: AI safety, alignment, interpretability, mechanistic interpretability, RLHF, scalable oversight, AI governance, red teaming, AI evaluations. Strict safety keyword filter removes false positives from broad terms. Up to 40 papers per week.

### Web Scrapers
| Organization | URL | Filter |
|---|---|---|
| Anthropic Alignment Science | alignment.anthropic.com | Blog posts with dates |
| Google DeepMind Safety | deepmind.google (responsible-development-and-safety) | Safety category |
| Apollo Research | apolloresearch.ai/blog | All blog posts |
| ARC (Alignment Research Center) | alignment.org/blog | Links containing `/blog/` |
| MIRI | intelligence.org/research | Links containing `/research/` |
| CAIS | safe.ai/research | Links to arxiv.org |
| FAR AI | far.ai/blog | Links containing `/news/` |
| UK AISI | aisi.gov.uk/work | Links containing `/blog/` |
| US AISI (NIST) | nist.gov | Links containing `/artificial-intelligence` |
| RAND | rand.org/topics/artificial-intelligence | All items |
| CSET Georgetown | cset.georgetown.edu/publications | Reports only (type-filtered) |
| CNAS | cnas.org/publications | AI/ML keyword filtered |
| GovAI Oxford | governance.ai/research | Links containing `/research-paper/` |
| IAPS | iaps.ai/research | Links containing `/research-paper/` |
| CLTR | longtermresilience.org/research | All items |
| CHAI Berkeley | humancompatible.ai/news | All items |
| MATS | matsprogram.org/research | Links containing `/research/` |
| Paul Christiano | paulfchristiano.com | All items |
| Yoshua Bengio | yoshuabengio.org (AI safety) | All items |
| Lennart Heim | blog.heim.xyz | All items |

### LessWrong
GraphQL API — posts with 150+ karma from the past 7 days.

### Twitter/X (optional)
Fetches recent tweets from curated accounts (Dean Ball, Seb Krier, Peter Wildeford) filtered by AI keywords. Requires `TWITTER_BEARER_TOKEN` env var (X API Basic tier). Gracefully skipped if no token is set.

### Trending
Reddit (r/aisafety, r/mlsafety, r/ControlProblem, min 250 upvotes) — research-filtered by URL domain and title keywords.

## How It Works

```
config.yaml → fetchers → 7-day date filter → dedup → research filter → enrich → render → GitHub Pages
```

1. **Fetch** — Six fetcher types (RSS, arXiv, scraper, LessWrong, Twitter/X, trending) collect papers
2. **Date filter** — Only papers from the last 7 days are kept. Scraped papers without parseable dates are dropped.
3. **Deduplicate** — Exact title match, then fuzzy matching (>85% similarity)
4. **Research filter** — 144-term scoring filter removes news/opinion. Non-research titles (hiring, policy, org updates) are rejected upfront. Known research orgs and arXiv need score >= 1, others >= 2.
5. **Enrich** — Papers with short/missing abstracts get them fetched from URLs or a synthetic fallback
6. **Render** — Jinja2 template produces a static site with featured section, org filters, and expandable abstracts

## Deployment

A GitHub Actions workflow runs every Monday at 9 AM UTC:

1. Fetches papers from all sources
2. Renders the site
3. Commits updated `data/papers.json` and `site/index.html`
4. Deploys to GitHub Pages

You can also trigger it manually from the Actions tab.

## Development

```bash
# Install dependencies
pip install -r requirements.txt  # Python 3.9+

# Fetch papers and render
python scripts/fetch.py
python scripts/render.py

# Or do both and open in browser
bash scripts/update-and-open.sh
```

### Adding a source

**RSS feed** — Add to `rss_feeds` in `config.yaml`:
```yaml
- name: "Example Lab"
  url: "https://example.com/feed.xml"
  org: "Example Lab"
  keywords: ["research", "paper", "model"]  # optional
  categories: ["Research"]                   # optional, filters by RSS <category> tags
```

**Web scraper** — Add to `scrapers` in `config.yaml`:
```yaml
- name: "Example Org"
  url: "https://example.com/research"
  org: "Example Org"
  link_must_contain: "/research/"  # optional
```

## License

MIT
