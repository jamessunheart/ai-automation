"""Apollo.io API integration for prospect data and enrichment"""

import requests
import os
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ApolloClient:
    """Apollo.io API client for B2B prospecting"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("APOLLO_API_KEY")
        if not self.api_key:
            raise ValueError("APOLLO_API_KEY not found in environment variables")

        self.base_url = "https://api.apollo.io/v1"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        })

    def search_people(
        self,
        job_titles: Optional[List[str]] = None,
        company_size: Optional[str] = "10-100",
        industries: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        page: int = 1,
        per_page: int = 25
    ) -> Dict:
        """
        Search for prospects matching ICP criteria

        Args:
            job_titles: List of job titles (e.g., ["CEO", "VP Marketing"])
            company_size: Employee count range (e.g., "10-100", "100-500")
            industries: List of industries (e.g., ["Software", "Marketing"])
            locations: List of locations (e.g., ["United States", "California"])
            keywords: Search keywords
            page: Page number (starts at 1)
            per_page: Results per page (max 100)

        Returns:
            Dict with 'people' list and pagination info
        """

        payload = {
            "api_key": self.api_key,
            "page": page,
            "per_page": min(per_page, 100)
        }

        # Add filters
        if job_titles:
            payload["person_titles"] = job_titles

        if company_size:
            # Convert to Apollo format
            size_ranges = {
                "1-10": ["1,10"],
                "10-50": ["11,50"],
                "10-100": ["11,100"],
                "50-200": ["51,200"],
                "100-500": ["101,500"],
                "500-1000": ["501,1000"],
                "1000+": ["1001,"]
            }
            payload["organization_num_employees_ranges"] = size_ranges.get(company_size, [company_size])

        if industries:
            # Apollo uses industry tag IDs - for now use keywords
            # TODO: Map industry names to Apollo tag IDs
            if not keywords:
                keywords = " OR ".join(industries)

        if locations:
            payload["person_locations"] = locations

        if keywords:
            payload["q_keywords"] = keywords

        try:
            response = self.session.post(
                f"{self.base_url}/mixed_people/search",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            logger.info(f"Apollo search returned {len(data.get('people', []))} results")

            return {
                "people": data.get("people", []),
                "pagination": data.get("pagination", {}),
                "total_results": data.get("pagination", {}).get("total_entries", 0)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo API error: {str(e)}")
            raise Exception(f"Failed to search people: {str(e)}")

    def enrich_person(
        self,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        domain: Optional[str] = None,
        linkedin_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Enrich person data with Apollo

        Args:
            email: Email address
            first_name: First name
            last_name: Last name
            domain: Company domain
            linkedin_url: LinkedIn profile URL

        Returns:
            Enriched person data or None if not found
        """

        payload = {
            "api_key": self.api_key
        }

        # Add available identifiers
        if email:
            payload["email"] = email
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if domain:
            payload["domain"] = domain
        if linkedin_url:
            payload["linkedin_url"] = linkedin_url

        try:
            response = self.session.post(
                f"{self.base_url}/people/match",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            person = data.get("person")

            if person:
                logger.info(f"Enriched person: {person.get('name')}")
                return person
            else:
                logger.warning(f"No match found for enrichment")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo enrichment error: {str(e)}")
            return None

    def get_contact_email(
        self,
        person_id: str
    ) -> Optional[str]:
        """
        Reveal email for a person (costs credits)

        Args:
            person_id: Apollo person ID

        Returns:
            Email address or None if not available
        """

        payload = {
            "api_key": self.api_key,
            "id": person_id
        }

        try:
            response = self.session.post(
                f"{self.base_url}/people/match",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            email = data.get("person", {}).get("email")

            if email:
                logger.info(f"Revealed email for person {person_id}")
                return email
            else:
                logger.warning(f"No email found for person {person_id}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo email reveal error: {str(e)}")
            return None

    def search_organizations(
        self,
        industries: Optional[List[str]] = None,
        employee_count: Optional[str] = None,
        revenue_range: Optional[str] = None,
        locations: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        page: int = 1,
        per_page: int = 25
    ) -> Dict:
        """
        Search for companies/organizations

        Args:
            industries: List of industries
            employee_count: Employee count range (e.g., "10-100")
            revenue_range: Revenue range (e.g., "$1M-$10M")
            locations: List of locations
            keywords: Search keywords
            page: Page number
            per_page: Results per page

        Returns:
            Dict with 'organizations' list and pagination info
        """

        payload = {
            "api_key": self.api_key,
            "page": page,
            "per_page": min(per_page, 100)
        }

        if employee_count:
            size_ranges = {
                "1-10": ["1,10"],
                "10-50": ["11,50"],
                "10-100": ["11,100"],
                "50-200": ["51,200"],
                "100-500": ["101,500"],
                "500-1000": ["501,1000"],
                "1000+": ["1001,"]
            }
            payload["organization_num_employees_ranges"] = size_ranges.get(employee_count, [employee_count])

        if locations:
            payload["organization_locations"] = locations

        if keywords:
            payload["q_organization_keyword_tags"] = keywords

        try:
            response = self.session.post(
                f"{self.base_url}/organizations/search",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            return {
                "organizations": data.get("organizations", []),
                "pagination": data.get("pagination", {}),
                "total_results": data.get("pagination", {}).get("total_entries", 0)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo organization search error: {str(e)}")
            raise Exception(f"Failed to search organizations: {str(e)}")

    def enrich_organization(
        self,
        domain: str
    ) -> Optional[Dict]:
        """
        Enrich company data

        Args:
            domain: Company domain (e.g., "acme.com")

        Returns:
            Enriched organization data or None if not found
        """

        payload = {
            "api_key": self.api_key,
            "domain": domain
        }

        try:
            response = self.session.post(
                f"{self.base_url}/organizations/enrich",
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            organization = data.get("organization")

            if organization:
                logger.info(f"Enriched organization: {organization.get('name')}")
                return organization
            else:
                logger.warning(f"No organization found for domain: {domain}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo organization enrichment error: {str(e)}")
            return None

    def format_prospect(self, person_data: Dict) -> Dict:
        """
        Format Apollo person data into standardized prospect format

        Args:
            person_data: Raw Apollo person data

        Returns:
            Formatted prospect dict
        """

        organization = person_data.get("organization", {}) or {}

        return {
            # Person info
            "apollo_id": person_data.get("id"),
            "first_name": person_data.get("first_name"),
            "last_name": person_data.get("last_name"),
            "name": person_data.get("name"),
            "email": person_data.get("email"),
            "email_status": person_data.get("email_status"),
            "linkedin_url": person_data.get("linkedin_url"),
            "title": person_data.get("title"),
            "seniority": person_data.get("seniority"),
            "departments": person_data.get("departments", []),

            # Company info
            "company_name": organization.get("name"),
            "company_domain": organization.get("website_url"),
            "company_industry": organization.get("industry"),
            "company_size": organization.get("estimated_num_employees"),
            "company_revenue": organization.get("estimated_annual_revenue"),
            "company_location": organization.get("city"),
            "company_country": organization.get("country"),

            # Technology
            "technologies": [tech.get("name") for tech in organization.get("technologies", [])],

            # Metadata
            "source": "apollo",
            "enriched_at": datetime.utcnow().isoformat()
        }

    def get_credit_balance(self) -> Dict:
        """
        Get Apollo API credit balance

        Returns:
            Dict with credit info
        """

        try:
            response = self.session.get(
                f"{self.base_url}/auth/health",
                params={"api_key": self.api_key},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            return {
                "credits_remaining": data.get("credits_remaining", 0),
                "daily_credits": data.get("daily_credits", 0),
                "monthly_credits": data.get("monthly_credits", 0)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Apollo credit check error: {str(e)}")
            return {
                "credits_remaining": 0,
                "daily_credits": 0,
                "monthly_credits": 0,
                "error": str(e)
            }


# Singleton instance
_apollo_client = None

def get_apollo_client() -> ApolloClient:
    """Get or create Apollo client singleton"""
    global _apollo_client
    if _apollo_client is None:
        _apollo_client = ApolloClient()
    return _apollo_client
