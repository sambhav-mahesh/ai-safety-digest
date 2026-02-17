#!/usr/bin/env python3
"""
Main orchestrator: fetch papers from all sources, deduplicate, filter for
research relevance, and write to data/papers.json.

Run from the project root:
    python scripts/fetch.py
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from collections import Counter

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that ``scripts.*`` imports work
# when the script is executed directly (e.g. ``python scripts/fetch.py``).
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.models import load_config, Paper
from scripts.fetchers.rss import fetch_rss
from scripts.fetchers.arxiv_fetcher import fetch_arxiv
from scripts.fetchers.scraper import fetch_scraped
from scripts.fetchers.lesswrong import fetch_lesswrong
from scripts.fetchers.trending import fetch_trending
from scripts.dedup import deduplicate
from scripts.enrich import enrich_abstracts

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "papers.json")


MAX_ABSTRACT_WORDS = 150

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")

# ---------------------------------------------------------------------------
# Research relevance scoring
# ---------------------------------------------------------------------------

# Terms that strongly indicate research content
_RESEARCH_TERMS = [
    "paper", "study", "model", "training", "benchmark", "evaluation",
    "dataset", "algorithm", "framework", "architecture", "fine-tuning",
    "fine tuning", "finetuning", "rlhf", "interpretability", "mechanistic",
    "alignment", "probe", "ablation", "embedding", "transformer", "neural",
    "gradient", "loss", "optimization", "inference", "scaling law",
    "emergent", "capability", "red team", "red-team", "safety",
    "robustness", "adversarial", "reward model", "constitutional",
    "reinforcement learning", "supervised learning", "pretraining",
    "pre-training", "backpropagation", "attention mechanism",
    "language model", "diffusion", "generative", "classification",
    "regression", "tokenizer", "tokenization", "perplexity", "accuracy",
    "precision", "recall", "f1 score", "auc", "roc", "cross-entropy",
    "softmax", "activation", "layer", "hidden state", "representation",
    "latent", "feature", "weight", "parameter", "hyperparameter",
    "convergence", "overfit", "regularization", "dropout", "batch",
    "epoch", "learning rate", "sgd", "adam", "llm", "gpt", "bert",
    "arxiv", "abstract", "methodology", "experiment", "result",
    "finding", "contribution", "technical report", "system card",
    "we propose", "we present", "we show", "we demonstrate",
    "we introduce", "we evaluate", "we find", "our method",
    "our approach", "our model", "state-of-the-art", "sota",
    "baseline", "comparison", "ablation study", "empirical",
    "theoretical", "formal", "proof", "theorem", "lemma",
    "proposition", "corollary", "analysis", "measurement",
    "quantitative", "qualitative", "survey", "review",
    "compute", "flops", "gpu", "tpu", "distributed training",
    "data augmentation", "curriculum learning", "knowledge distillation",
    "multi-task", "transfer learning", "zero-shot", "few-shot",
    "in-context learning", "chain of thought", "prompting",
    "jailbreak", "guardrail", "watermark", "detection",
    "deception", "sycophancy", "power-seeking", "corrigibility",
    "oversight", "monitor", "audit", "specification",
]

# Organizations that are known research producers — give them a lower bar
_RESEARCH_ORGS = {
    "anthropic", "openai", "google deepmind", "microsoft research",
    "redwood research", "alignment forum", "metr", "apollo research",
    "arc", "miri", "cais", "far ai", "uk aisi", "us aisi",
    "epoch ai", "chai", "mats", "govai", "cset", "iaps", "cltr",
    "rand", "dan hendrycks", "paul christiano", "yoshua bengio",
    "lennart heim", "fli", "lesswrong",
}

# Minimum score thresholds
_SCORE_THRESHOLD_DEFAULT = 2    # general sources need at least 2 matching terms
_SCORE_THRESHOLD_RESEARCH_ORG = 1  # known research orgs need at least 1


def _is_research_relevant(paper: Paper) -> bool:
    """
    Score a paper for research relevance based on title + abstract content.

    Uses a term-matching approach:
    - Papers from arXiv always pass (source_type == "arxiv").
    - Papers from known research orgs have a lower threshold.
    - Other papers need a higher score to pass.

    Returns True if the paper should be kept.
    """
    # arXiv papers are always research
    if paper.source_type == "arxiv":
        return True

    searchable = (paper.title + " " + paper.abstract).lower()

    # Count how many distinct research terms appear
    score = 0
    for term in _RESEARCH_TERMS:
        if term in searchable:
            score += 1

    # Determine the threshold based on organization
    org_lower = paper.organization.lower()
    if org_lower in _RESEARCH_ORGS:
        threshold = _SCORE_THRESHOLD_RESEARCH_ORG
    else:
        threshold = _SCORE_THRESHOLD_DEFAULT

    return score >= threshold


def _clean_abstract(text: str) -> str:
    """Strip HTML, collapse whitespace, and cap at 150 words."""
    if not text:
        return ""
    # Strip HTML tags
    text = _HTML_TAG_RE.sub(" ", text)
    # Collapse whitespace
    text = _WHITESPACE_RE.sub(" ", text).strip()
    # Remove "Published on ..." date prefixes common in RSS
    text = re.sub(
        r"^Published on [A-Z][a-z]+ \d{1,2}, \d{4}\s*\d*:?\d*\s*[AP]?M?\s*GMT\s*",
        "",
        text,
    )
    # Remove "Blog Category * Date" prefixes from scraped UK AISI etc.
    text = re.sub(
        r"^(?:Blog|Research|Report|Paper)\s+[\w\s&]+\u2022\s*"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\s*",
        "",
        text,
    )
    # Remove leading date patterns like "16 May 2024" or "May 2024"
    text = re.sub(
        r"^\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*",
        "",
        text,
    )
    text = text.strip()
    # Cap at 150 words
    words = text.split()
    if len(words) > MAX_ABSTRACT_WORDS:
        truncated = " ".join(words[:MAX_ABSTRACT_WORDS])
        # Try to cut at a sentence boundary
        last_period = truncated.rfind(". ")
        if last_period > len(truncated) * 0.5:
            return truncated[: last_period + 1]
        return truncated + "..."
    return text


def main() -> None:
    logger.info("Loading configuration from %s", CONFIG_PATH)
    config = load_config(CONFIG_PATH)

    # ------------------------------------------------------------------
    # Fetch from each source
    # ------------------------------------------------------------------
    all_papers: list[Paper] = []

    # RSS feeds
    rss_feeds_cfg = config.get("rss_feeds", [])
    if rss_feeds_cfg:
        logger.info("Fetching RSS feeds (%d configured)", len(rss_feeds_cfg))
        rss_papers = fetch_rss(rss_feeds_cfg)
        all_papers.extend(rss_papers)
    else:
        logger.info("No RSS feeds configured; skipping")

    # arXiv
    arxiv_cfg = config.get("arxiv", {})
    if arxiv_cfg:
        logger.info("Fetching arXiv papers")
        arxiv_papers = fetch_arxiv(arxiv_cfg)
        all_papers.extend(arxiv_papers)
    else:
        logger.info("No arXiv config found; skipping")

    # Web scrapers
    scrapers_cfg = config.get("scrapers", [])
    if scrapers_cfg:
        logger.info("Fetching scraped sites (%d configured)", len(scrapers_cfg))
        scraped_papers = fetch_scraped(scrapers_cfg)
        all_papers.extend(scraped_papers)
    else:
        logger.info("No scrapers configured; skipping")

    # LessWrong (high-karma)
    lw_cfg = config.get("lesswrong", {})
    if lw_cfg:
        logger.info("Fetching LessWrong posts (min karma: %d)", lw_cfg.get("min_karma", 100))
        lw_papers = fetch_lesswrong(lw_cfg)
        all_papers.extend(lw_papers)
    else:
        logger.info("No LessWrong config found; skipping")

    # Trending (HN + Reddit)
    trending_cfg = config.get("trending", {})
    if trending_cfg:
        logger.info("Fetching trending content (HN + Reddit)")
        trending_papers = fetch_trending(trending_cfg)
        all_papers.extend(trending_papers)
    else:
        logger.info("No trending config found; skipping")

    logger.info("Total papers before deduplication: %d", len(all_papers))

    # ------------------------------------------------------------------
    # Deduplicate
    # ------------------------------------------------------------------
    papers = deduplicate(all_papers)

    # ------------------------------------------------------------------
    # Research relevance filter — remove non-research content
    # ------------------------------------------------------------------
    pre_filter_count = len(papers)
    papers = [p for p in papers if _is_research_relevant(p)]
    filtered_out = pre_filter_count - len(papers)
    logger.info(
        "Research relevance filter: kept %d, removed %d of %d",
        len(papers),
        filtered_out,
        pre_filter_count,
    )

    # ------------------------------------------------------------------
    # Enrich papers with missing or short abstracts
    # ------------------------------------------------------------------
    papers = enrich_abstracts(papers)

    # ------------------------------------------------------------------
    # Clean and cap all abstracts at 150 words
    # ------------------------------------------------------------------
    for p in papers:
        p.abstract = _clean_abstract(p.abstract)

    # ------------------------------------------------------------------
    # Sort by published_date descending
    # ------------------------------------------------------------------
    papers.sort(key=lambda p: p.published_date, reverse=True)

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    papers_dicts = [p.to_dict() for p in papers]
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(papers_dicts, f, indent=2, ensure_ascii=False)

    logger.info("Wrote %d papers to %s", len(papers), OUTPUT_PATH)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    counts = Counter(p.source_type for p in papers)
    logger.info("--- Summary ---")
    for source_type in ("rss", "arxiv", "scrape"):
        logger.info("  %-8s %d papers", source_type, counts.get(source_type, 0))
    logger.info("  %-8s %d papers", "TOTAL", len(papers))


if __name__ == "__main__":
    main()
