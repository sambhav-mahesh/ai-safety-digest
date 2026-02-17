"""Fetch papers from arXiv using the arxiv Python package."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import arxiv

from scripts.models import Paper

logger = logging.getLogger(__name__)


def _build_query(keywords: list[str], categories: list[str]) -> str:
    """
    Build an arXiv API query string.

    Format:
        (ti:"kw1" OR ti:"kw2" OR ...) AND (cat:cs.AI OR cat:cs.LG OR ...)
    """
    keyword_clauses = " OR ".join(f'ti:"{kw}"' for kw in keywords)
    category_clauses = " OR ".join(f"cat:{cat}" for cat in categories)
    return f"({keyword_clauses}) AND ({category_clauses})"


def _extract_organization(result) -> str:
    """
    Try to pull an affiliation from the first author.

    The arXiv API rarely exposes affiliations, so fall back to 'arXiv'.
    """
    try:
        authors = result.authors
        if authors:
            first_author = authors[0]
            # The arxiv package may expose affiliations as a list (non-standard)
            affiliations = getattr(first_author, "affiliations", None)
            if affiliations:
                return affiliations[0]
    except Exception:
        pass
    return "arXiv"


def fetch_arxiv(arxiv_config: dict) -> list[Paper]:
    """
    Fetch papers from arXiv matching the configured keywords and categories.

    Parameters
    ----------
    arxiv_config : dict
        Must contain ``keywords``, ``categories``, ``max_results``, and
        ``days_back``.

    Returns
    -------
    list[Paper]
    """
    keywords: list[str] = arxiv_config.get("keywords", [])
    categories: list[str] = arxiv_config.get("categories", [])
    max_results: int = arxiv_config.get("max_results", 40)
    days_back: int = arxiv_config.get("days_back", 7)

    if not keywords or not categories:
        logger.warning("arXiv config missing keywords or categories; skipping")
        return []

    query = _build_query(keywords, categories)
    logger.info("arXiv query: %s", query)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    papers: list[Paper] = []

    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        for result in client.results(search):
            # result.published is a datetime (usually UTC)
            pub_date = result.published
            if pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            if pub_date < cutoff:
                continue

            authors = [a.name for a in result.authors]
            organization = _extract_organization(result)

            papers.append(
                Paper(
                    title=result.title.strip(),
                    authors=authors,
                    organization=organization,
                    abstract=result.summary.strip(),
                    url=result.entry_id,
                    published_date=pub_date.isoformat(),
                    source_type="arxiv",
                    source_url="https://arxiv.org/",
                )
            )

        logger.info("arXiv: %d papers collected", len(papers))

    except Exception:
        logger.warning("Failed to fetch from arXiv", exc_info=True)

    return papers
