"""Prospect management API endpoints"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
import logging

from .integrations.apollo import get_apollo_client
from .tracking import tracker, EventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prospects", tags=["prospects"])


class ProspectSearchRequest(BaseModel):
    """Request model for prospect search"""
    job_titles: Optional[List[str]] = None
    company_size: Optional[str] = "10-100"
    industries: Optional[List[str]] = None
    locations: Optional[List[str]] = ["United States"]
    keywords: Optional[str] = None
    page: int = 1
    per_page: int = 25


class ProspectEnrichRequest(BaseModel):
    """Request model for prospect enrichment"""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    domain: Optional[str] = None
    linkedin_url: Optional[str] = None


@router.post("/search")
async def search_prospects(request: ProspectSearchRequest):
    """
    Search for prospects using Apollo.io

    Example:
    ```json
    {
        "job_titles": ["CEO", "Founder", "VP Marketing"],
        "company_size": "10-100",
        "industries": ["Software", "SaaS"],
        "locations": ["United States"],
        "per_page": 25
    }
    ```
    """
    try:
        apollo = get_apollo_client()

        results = apollo.search_people(
            job_titles=request.job_titles,
            company_size=request.company_size,
            industries=request.industries,
            locations=request.locations,
            keywords=request.keywords,
            page=request.page,
            per_page=request.per_page
        )

        # Format prospects
        prospects = [apollo.format_prospect(person) for person in results.get("people", [])]

        return {
            "success": True,
            "prospects": prospects,
            "total_results": results.get("total_results", 0),
            "page": request.page,
            "per_page": request.per_page,
            "has_more": len(prospects) == request.per_page
        }

    except Exception as e:
        logger.error(f"Prospect search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/enrich")
async def enrich_prospect(request: ProspectEnrichRequest):
    """
    Enrich prospect data using Apollo.io

    Example:
    ```json
    {
        "email": "john@acme.com"
    }
    ```
    """
    try:
        apollo = get_apollo_client()

        person = apollo.enrich_person(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            domain=request.domain,
            linkedin_url=request.linkedin_url
        )

        if not person:
            raise HTTPException(status_code=404, detail="No match found")

        prospect = apollo.format_prospect(person)

        return {
            "success": True,
            "prospect": prospect
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prospect enrichment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {str(e)}")


@router.get("/credits")
async def get_credits():
    """Get Apollo API credit balance"""
    try:
        apollo = get_apollo_client()
        credits = apollo.get_credit_balance()

        return {
            "success": True,
            "credits": credits
        }

    except Exception as e:
        logger.error(f"Credit check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Credit check failed: {str(e)}")


@router.post("/import-to-campaign")
async def import_prospects_to_campaign(
    campaign_id: str,
    job_titles: List[str] = Query(...),
    company_size: str = Query("10-100"),
    industries: Optional[List[str]] = Query(None),
    locations: List[str] = Query(["United States"]),
    limit: int = Query(100, le=1000)
):
    """
    Search prospects and import them to a campaign

    This will:
    1. Search Apollo for prospects matching criteria
    2. Format prospect data
    3. Log them as analyzed prospects
    4. Return prospect list for campaign use

    Query Parameters:
    - campaign_id: Campaign ID to associate prospects with
    - job_titles: Job titles to search for
    - company_size: Company size range (e.g., "10-100")
    - industries: Industries to target
    - locations: Geographic locations
    - limit: Max number of prospects to import
    """
    try:
        apollo = get_apollo_client()

        # Calculate pages needed
        per_page = 100
        pages_needed = (limit + per_page - 1) // per_page

        all_prospects = []

        for page in range(1, pages_needed + 1):
            results = apollo.search_people(
                job_titles=job_titles,
                company_size=company_size,
                industries=industries,
                locations=locations,
                page=page,
                per_page=min(per_page, limit - len(all_prospects))
            )

            prospects = [apollo.format_prospect(person) for person in results.get("people", [])]
            all_prospects.extend(prospects)

            # Log prospects as analyzed
            for prospect in prospects:
                tracker.log_event(
                    EventType.PROSPECT_ANALYZED,
                    campaign_id,
                    {
                        "prospect_email": prospect.get("email"),
                        "prospect_name": prospect.get("name"),
                        "company": prospect.get("company_name"),
                        "title": prospect.get("title"),
                        "source": "apollo"
                    }
                )

            if len(all_prospects) >= limit:
                break

            if not results.get("has_more", False):
                break

        return {
            "success": True,
            "campaign_id": campaign_id,
            "prospects_imported": len(all_prospects),
            "prospects": all_prospects
        }

    except Exception as e:
        logger.error(f"Prospect import error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/search/saved")
async def get_saved_searches():
    """Get saved prospect search templates (ICP definitions)"""

    # These are example ICPs - in production, load from database
    saved_searches = [
        {
            "id": "saas_founders",
            "name": "SaaS Founders & CEOs",
            "description": "Early-stage SaaS founders, 10-100 employees",
            "criteria": {
                "job_titles": ["CEO", "Founder", "Co-Founder"],
                "company_size": "10-100",
                "industries": ["Computer Software", "Internet", "SaaS"],
                "locations": ["United States"]
            }
        },
        {
            "id": "marketing_vps",
            "name": "Marketing VPs at Growing Companies",
            "description": "VP Marketing at 50-500 employee companies",
            "criteria": {
                "job_titles": ["VP Marketing", "VP of Marketing", "Head of Marketing"],
                "company_size": "50-500",
                "industries": ["Marketing", "Advertising", "Computer Software"],
                "locations": ["United States"]
            }
        },
        {
            "id": "agency_owners",
            "name": "Marketing Agency Owners",
            "description": "Agency founders and owners",
            "criteria": {
                "job_titles": ["CEO", "Founder", "Owner", "President"],
                "company_size": "10-50",
                "industries": ["Marketing and Advertising", "Public Relations"],
                "locations": ["United States"]
            }
        }
    ]

    return {
        "success": True,
        "saved_searches": saved_searches
    }
