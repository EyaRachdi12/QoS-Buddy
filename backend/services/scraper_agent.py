"""
Scraper Agent: complementary metadata from open data portals (never writes unified CSV).
Uses API-first sources + light HTML for UCI seeds; rate-limited requests.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Set

import requests
from bs4 import BeautifulSoup

from core.config import (
    DATAGOV_CKAN_API,
    EU_DATA_API,
    SCRAPER_MIN_DELAY_SEC,
    SCRAPER_REQUEST_TIMEOUT_SEC,
    SCRAPED_CATALOG_JSON,
    SCRAPER_SEEDS_JSON,
    TELECOM_RELEVANCE_THRESHOLD,
    UCI_SEEDS_JSON,
)
from core.schemas import ExternalDatasetRecord

TELECOM_KEYWORDS = re.compile(
    r"telecom|telecommunication|broadband|network|qos|latency|packet|5g|lte|nr\b|"
    r"wireless|cellular|backbone|traffic|routing|fiber|fibre|spectrum|mobile",
    re.I,
)

GITHUB_AWS_DATASETS_API = (
    "https://api.github.com/repos/awslabs/open-data-registry/contents/datasets"
)


def _score_text(text: str) -> float:
    if not text:
        return 0.0
    hits = len(TELECOM_KEYWORDS.findall(text))
    return min(1.0, hits * 0.22)


def _sleep():
    if SCRAPER_MIN_DELAY_SEC > 0:
        time.sleep(SCRAPER_MIN_DELAY_SEC)


class ScraperAgent:
    def fetch_datagov(self, rows: int = 15) -> List[ExternalDatasetRecord]:
        out: List[ExternalDatasetRecord] = []
        q = "telecommunication OR broadband OR network OR qos OR lte"
        params = {"q": q, "rows": rows}
        _sleep()
        r = requests.get(
            DATAGOV_CKAN_API,
            params=params,
            timeout=SCRAPER_REQUEST_TIMEOUT_SEC,
            headers={"User-Agent": "QoSBuddy/1.0 (research)"},
        )
        r.raise_for_status()
        payload = r.json()
        res = (payload.get("result") or {}).get("results") or []
        for pkg in res:
            title = pkg.get("title") or pkg.get("name") or "untitled"
            url = pkg.get("url") or f"https://catalog.data.gov/dataset/{pkg.get('name','')}"
            notes = pkg.get("notes") or ""
            tags = [
                t.get("name")
                for t in (pkg.get("tags") or [])
                if isinstance(t, dict) and t.get("name")
            ][:12]
            rec = ExternalDatasetRecord(
                title=str(title)[:500],
                source_portal="data.gov",
                url=str(url)[:2000],
                description=str(notes)[:1500] or None,
                license=None,
                telecom_tags=[t for t in tags if TELECOM_KEYWORDS.search(str(t))],
                relevance_score=_score_text(f"{title} {notes} {' '.join(tags)}"),
            )
            if rec.relevance_score >= TELECOM_RELEVANCE_THRESHOLD:
                out.append(rec)
        return out

    def fetch_eu_datasets(self, limit: int = 15) -> List[ExternalDatasetRecord]:
        out: List[ExternalDatasetRecord] = []
        params = {"query": "telecommunication network broadband QoS mobile", "limit": limit}
        _sleep()
        r = requests.get(
            EU_DATA_API,
            params=params,
            timeout=SCRAPER_REQUEST_TIMEOUT_SEC,
            headers={"User-Agent": "QoSBuddy/1.0 (research)"},
        )
        if r.status_code != 200:
            return out
        payload = r.json()
        results = payload
        if isinstance(payload, dict):
            results = (
                payload.get("datasets")
                or payload.get("results")
                or payload.get("data")
                or []
            )
        if not isinstance(results, list):
            return out
        for item in results[:limit]:
            if not isinstance(item, dict):
                continue
            title = item.get("title") or item.get("name") or "untitled"
            url = (
                item.get("landingPage")
                or item.get("url")
                or item.get("id")
                or "https://data.europa.eu/"
            )
            desc = item.get("description") or item.get("summary") or ""
            text = f"{title} {desc}"
            rec = ExternalDatasetRecord(
                title=str(title)[:500],
                source_portal="data.europa.eu",
                url=str(url)[:2000],
                description=str(desc)[:1500] or None,
                relevance_score=_score_text(text),
            )
            if rec.relevance_score >= TELECOM_RELEVANCE_THRESHOLD:
                out.append(rec)
        return out

    def fetch_aws_registry_samples(self, max_files: int = 40) -> List[ExternalDatasetRecord]:
        """List YAML entries from AWS Open Data Registry GitHub; filter by telecom keywords."""
        out: List[ExternalDatasetRecord] = []
        _sleep()
        r = requests.get(
            GITHUB_AWS_DATASETS_API,
            params={"per_page": min(100, max_files * 3)},
            timeout=SCRAPER_REQUEST_TIMEOUT_SEC,
            headers={"User-Agent": "QoSBuddy/1.0 (research)"},
        )
        if r.status_code != 200:
            return out
        items = r.json()
        if not isinstance(items, list):
            return out
        for item in items:
            if not isinstance(item, dict) or item.get("type") != "file":
                continue
            name = item.get("name") or ""
            if not name.endswith((".yaml", ".yml")):
                continue
            slug = name.rsplit(".", 1)[0]
            title = slug.replace("-", " ").title()
            url = f"https://registry.opendata.aws/datasets/{slug}/"
            text = f"{title} {slug}"
            score = _score_text(text)
            if score < TELECOM_RELEVANCE_THRESHOLD:
                continue
            out.append(
                ExternalDatasetRecord(
                    title=title[:500],
                    source_portal="registry.opendata.aws",
                    url=url,
                    description=f"Open Data Registry dataset slug: {slug}",
                    telecom_tags=[slug],
                    relevance_score=score,
                )
            )
            if len(out) >= max_files:
                break
        return out

    def fetch_uci_seeds(self) -> List[ExternalDatasetRecord]:
        out: List[ExternalDatasetRecord] = []
        if not UCI_SEEDS_JSON.exists():
            return out
        try:
            data = json.loads(UCI_SEEDS_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return out
        for seed in data.get("seeds", [])[:12]:
            url = seed.get("url")
            if not url:
                continue
            note = seed.get("note") or ""
            _sleep()
            try:
                r = requests.get(
                    url,
                    timeout=SCRAPER_REQUEST_TIMEOUT_SEC,
                    headers={"User-Agent": "QoSBuddy/1.0 (research)"},
                )
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                og = soup.find("meta", property="og:title")
                title = og["content"] if og and og.get("content") else None
                if not title and soup.title and soup.title.string:
                    title = soup.title.string.strip()
                if not title:
                    title = url
                desc_tag = soup.find("meta", attrs={"name": "description"})
                desc = desc_tag["content"] if desc_tag and desc_tag.get("content") else note
                text = f"{title} {desc}"
                score = max(_score_text(text), TELECOM_RELEVANCE_THRESHOLD - 0.05)
                out.append(
                    ExternalDatasetRecord(
                        title=str(title)[:500],
                        source_portal="archive.ics.uci.edu",
                        url=str(url)[:2000],
                        description=str(desc)[:1500],
                        relevance_score=min(1.0, score + 0.1),
                    )
                )
            except Exception:
                out.append(
                    ExternalDatasetRecord(
                        title=str(url),
                        source_portal="archive.ics.uci.edu",
                        url=str(url),
                        description=note,
                        relevance_score=TELECOM_RELEVANCE_THRESHOLD,
                    )
                )
        return out

    def fetch_manual_seeds(self) -> List[ExternalDatasetRecord]:
        out: List[ExternalDatasetRecord] = []
        if not SCRAPER_SEEDS_JSON.exists():
            return out
        try:
            data = json.loads(SCRAPER_SEEDS_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return out
        for item in data.get("google_dataset_landing_pages", [])[:20]:
            if isinstance(item, str):
                url = item
                src = "manual"
            elif isinstance(item, dict):
                url = item.get("url")
                src = item.get("source_portal", "manual")
            else:
                continue
            if not url:
                continue
            out.append(
                ExternalDatasetRecord(
                    title=str(url)[:240],
                    source_portal=str(src),
                    url=str(url)[:2000],
                    relevance_score=TELECOM_RELEVANCE_THRESHOLD,
                )
            )
        return out

    def run_all(self) -> tuple[List[ExternalDatasetRecord], List[str]]:
        errors: List[str] = []
        all_recs: List[ExternalDatasetRecord] = []

        for name, fn in (
            ("data.gov", lambda: self.fetch_datagov()),
            ("data.europa.eu", lambda: self.fetch_eu_datasets()),
            ("aws_registry", lambda: self.fetch_aws_registry_samples()),
            ("uci_seeds", lambda: self.fetch_uci_seeds()),
            ("manual_seeds", lambda: self.fetch_manual_seeds()),
        ):
            try:
                all_recs.extend(fn())
            except Exception as e:
                errors.append(f"{name}: {e}")

        seen: Set[str] = set()
        unique: List[ExternalDatasetRecord] = []
        for r in all_recs:
            key = (r.url, r.title)
            if key in seen:
                continue
            seen.add(key)
            unique.append(r)
        return unique, errors

    def save_catalog(self, records: List[ExternalDatasetRecord]) -> int:
        SCRAPED_CATALOG_JSON.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "records": [json.loads(r.model_dump_json()) for r in records],
        }
        SCRAPED_CATALOG_JSON.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return len(records)

    def load_catalog(self) -> List[ExternalDatasetRecord]:
        if not SCRAPED_CATALOG_JSON.exists():
            return []
        try:
            data = json.loads(SCRAPED_CATALOG_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        recs = data.get("records") if isinstance(data, dict) else data
        if not isinstance(recs, list):
            return []
        out: List[ExternalDatasetRecord] = []
        for item in recs:
            if isinstance(item, dict):
                try:
                    out.append(ExternalDatasetRecord(**item))
                except Exception:
                    continue
        return out
