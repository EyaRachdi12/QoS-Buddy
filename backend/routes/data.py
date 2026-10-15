"""Data refresh, enrichment, and source-BO summary routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends

from core.schemas import DataRefreshResponse, EnrichmentCatalogResponse, EnrichmentScrapeResponse
from routes.deps import get_orchestrator, get_current_user_optional
from services.dataset_profile import get_source_bo_distribution, invalidate_source_bo_cache
from services.scraper_agent import ScraperAgent

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/data/source-bo-summary")
async def source_bo_summary(_user=Depends(get_current_user_optional)):
    return get_source_bo_distribution()


@router.post("/data/refresh", response_model=DataRefreshResponse)
async def data_refresh(_user=Depends(get_current_user_optional)):
    orchestrator = get_orchestrator()
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not available")

    invalidate_source_bo_cache()
    df, status = orchestrator.refresh_data(force=True)
    path = orchestrator.data_manager.resolved_path()
    mtime = None
    if path.exists():
        mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
    rows = len(df) if df is not None else 0
    return DataRefreshResponse(
        success=df is not None,
        timestamp=datetime.now().isoformat(),
        rows=rows,
        source_path=str(path),
        mtime=mtime,
    )


@router.get("/enrichment/catalog", response_model=EnrichmentCatalogResponse)
async def enrichment_catalog(offset: int = 0, limit: int = 50, _user=Depends(get_current_user_optional)):
    scraper = ScraperAgent()
    all_recs = scraper.load_catalog()
    total = len(all_recs)
    slice_recs = all_recs[offset : offset + limit]
    return EnrichmentCatalogResponse(
        success=True,
        total=total,
        offset=offset,
        limit=limit,
        records=slice_recs,
    )


@router.post("/enrichment/scrape", response_model=EnrichmentScrapeResponse)
async def enrichment_scrape(_user=Depends(get_current_user_optional)):
    scraper = ScraperAgent()
    records, errors = scraper.run_all()
    n = scraper.save_catalog(records)
    return EnrichmentScrapeResponse(
        success=len(errors) == 0,
        timestamp=datetime.now().isoformat(),
        added=len(records),
        total_in_catalog=n,
        errors=errors,
    )
