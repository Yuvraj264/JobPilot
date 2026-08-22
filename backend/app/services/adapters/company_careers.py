import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse

import httpx
from app.database.connection import SessionLocal
from app.models.job import SourceConfiguration, JobSource
from app.services.adapters.base import (
    JobSourceAdapter,
    AdapterError,
    AuthenticationRequiredError,
    RateLimitedError,
    AccessRestrictedError,
    NetworkError,
    ParsingError,
    UnsupportedOperationError,
)

logger = logging.getLogger(__name__)


def run_async(coro):
    """Safely runs async coroutines in a separate thread to prevent event loop collision in FastAPI."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(lambda: asyncio.new_event_loop().run_until_complete(coro))
        return future.result()


class CompanyCareersJobSourceAdapter(JobSourceAdapter):
    """
    Generic Company Career Portal Adapter.
    Supports DOM scraping, JSON-LD parsing, Greenhouse public Job Board API, and Lever public Postings API.
    """

    def source_name(self) -> str:
        return "company_careers"

    def display_name(self) -> str:
        return "Company Career Pages"

    def source_type(self) -> str:
        return "WEB"

    def discover_jobs(self, limit: int = 50, page: int = 1) -> List[Dict[str, Any]]:
        """
        Discovers jobs. If specific target configuration is set in the thread-local context or DB, uses it.
        Otherwise, runs discovery across all enabled company career configurations.
        """
        db = SessionLocal()
        try:
            # Fetch all enabled configurations for company careers
            source = db.query(JobSource).filter(JobSource.name == self.source_name()).first()
            if not source:
                return []
            
            configs = db.query(SourceConfiguration).filter(
                SourceConfiguration.source_id == source.id,
                SourceConfiguration.enabled == True,
                SourceConfiguration.discovery_enabled == True
            ).all()
            
            all_discovered_jobs = []
            for config_record in configs:
                config_data = config_record.configuration
                if not config_data:
                    continue
                
                try:
                    jobs = self._discover_single_company(config_data, limit, page)
                    all_discovered_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"Error discovering jobs for company {config_data.get('company_name', 'Unknown')}: {e}")
                    # Don't fail the whole run if one company fails
                    continue
            
            return all_discovered_jobs
        finally:
            db.close()

    def get_job_details(self, external_id: str) -> Optional[Dict[str, Any]]:
        # Single job detail retrieval is normally done during listing traversal,
        # but let's implement a fallback
        return None

    def health_check(self) -> str:
        # A generic health check; will verify if we can make network requests
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get("https://boards-api.greenhouse.io/v1/boards/stripe/jobs", follow_redirects=True)
                if res.status_code == 200:
                    return "healthy"
                elif res.status_code == 429:
                    return "rate_limited"
                else:
                    return "available"
        except Exception:
            return "error"

    def metadata(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name(),
            "display_name": self.display_name(),
            "source_type": self.source_type(),
            "supported_access_method": "DOM Scraping / JSON-LD / Greenhouse API / Lever API",
            "requires_authentication": False,
            "requires_human_interaction": False,
            "automation_allowed": True,
            "capabilities": {
                "DISCOVERY": True,
                "APPLICATION": False,
                "BROWSER": True,
                "API": True,
                "FEED": True,
                "HUMAN_ASSISTED": False,
            },
            "notes": "Flexible generic adapter supporting standard modern ATS endpoints and custom DOM paths.",
        }

    def _discover_single_company(self, config: Dict[str, Any], limit: int, page: int) -> List[Dict[str, Any]]:
        """Invokes the appropriate discovery method for a company configuration."""
        method = config.get("discovery_method", "DOM_SELECTORS").upper()
        careers_url = config.get("careers_url")
        company_name = config.get("company_name", "Unknown Company")
        
        if not careers_url:
            raise ValueError(f"Missing careers_url in configuration for {company_name}")

        from app.services.url_security_service import URLSecurityService
        URLSecurityService.validate_url(careers_url)

        logger.info(f"Starting discovery for {company_name} using method: {method}")

        if method == "GREENHOUSE_API":
            board_token = config.get("board_token") or urlparse(careers_url).path.split("/")[-1]
            return self._discover_greenhouse(board_token, company_name)
        elif method == "LEVER_API":
            company_id = config.get("company_id") or urlparse(careers_url).path.split("/")[-1]
            return self._discover_lever(company_id, company_name)
        elif method == "JSON_LD":
            return self._discover_json_ld(careers_url, company_name)
        elif method == "DOM_SELECTORS":
            return self._discover_dom_selectors(careers_url, company_name, config.get("parser_configuration", {}), limit, page)
        else:
            raise UnsupportedOperationError(f"Unsupported discovery method: {method}")

    # --- GREENHOUSE ---
    def _discover_greenhouse(self, board_token: str, company_name: str) -> List[Dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        try:
            res = httpx.get(url, timeout=10.0, follow_redirects=True)
            if res.status_code == 429:
                raise RateLimitedError("Greenhouse API rate limit exceeded")
            if res.status_code == 404:
                raise SourceUnavailableError("Greenhouse board not found")
            res.raise_for_status()
            data = res.json()
            jobs = data.get("jobs", [])
            
            results = []
            for j in jobs:
                results.append({
                    "external_id": f"greenhouse-{j.get('id')}",
                    "title": j.get("title"),
                    "company": company_name,
                    "location": j.get("location", {}).get("name") if j.get("location") else None,
                    "description": j.get("content"),
                    "job_url": j.get("absolute_url"),
                    "application_url": j.get("absolute_url"),
                    "metadata": {"source_type": "Greenhouse API", "raw_id": j.get("id")}
                })
            return results
        except httpx.HTTPError as he:
            raise NetworkError(f"Greenhouse network error: {he}")

    # --- LEVER ---
    def _discover_lever(self, company_id: str, company_name: str) -> List[Dict[str, Any]]:
        url = f"https://api.lever.co/v0/postings/{company_id}"
        try:
            res = httpx.get(url, timeout=10.0, follow_redirects=True)
            if res.status_code == 429:
                raise RateLimitedError("Lever API rate limit exceeded")
            if res.status_code == 404:
                raise SourceUnavailableError("Lever company page not found")
            res.raise_for_status()
            jobs = res.json()
            
            results = []
            for j in jobs:
                results.append({
                    "external_id": f"lever-{j.get('id')}",
                    "title": j.get("text"),
                    "company": company_name,
                    "location": j.get("categories", {}).get("location"),
                    "description": j.get("descriptionPlain") or j.get("additionalPlain"),
                    "job_url": j.get("hostedUrl"),
                    "application_url": j.get("hostedUrl"),
                    "employment_type": j.get("categories", {}).get("commitment"),
                    "metadata": {"source_type": "Lever API", "raw_id": j.get("id")}
                })
            return results
        except httpx.HTTPError as he:
            raise NetworkError(f"Lever network error: {he}")

    # --- JSON-LD ---
    def _discover_json_ld(self, url: str, company_name: str) -> List[Dict[str, Any]]:
        try:
            res = httpx.get(url, timeout=10.0, follow_redirects=True)
            res.raise_for_status()
            html = res.text
            
            json_ld_blocks = re.findall(r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
            
            jobs = []
            for block in json_ld_blocks:
                try:
                    data = json.loads(block.strip())
                    if isinstance(data, dict):
                        data = [data]
                    
                    for item in data:
                        if item.get("@type") == "JobPosting":
                            title = item.get("title")
                            desc = item.get("description")
                            desc_clean = re.sub(r'<[^>]*>', ' ', desc) if desc else ""
                            
                            company = item.get("hiringOrganization", {}).get("name") or company_name
                            
                            loc_info = item.get("jobLocation")
                            loc_name = None
                            if isinstance(loc_info, dict):
                                address = loc_info.get("address")
                                if isinstance(address, dict):
                                    loc_name = address.get("addressLocality") or address.get("addressRegion")
                                elif isinstance(address, str):
                                    loc_name = address
                            
                            ext_id = item.get("identifier", {}).get("value") or item.get("identifier")
                            if not ext_id:
                                ext_id = f"ld-{hash(f'{title}-{company}-{loc_name}')}"
                                
                            salary_min = None
                            salary_max = None
                            salary_curr = "USD"
                            salary_info = item.get("baseSalary")
                            if isinstance(salary_info, dict):
                                val_info = salary_info.get("value")
                                salary_curr = salary_info.get("currency") or "USD"
                                if isinstance(val_info, dict):
                                    salary_min = val_info.get("minValue") or val_info.get("value")
                                    salary_max = val_info.get("maxValue") or val_info.get("value")
                                elif isinstance(val_info, (int, float)):
                                    salary_min = val_info
                                    
                            jobs.append({
                                "external_id": str(ext_id),
                                "title": title,
                                "company": company,
                                "location": loc_name,
                                "description": desc_clean.strip(),
                                "job_url": item.get("url") or url,
                                "application_url": item.get("url") or url,
                                "employment_type": item.get("employmentType"),
                                "salary_min": salary_min,
                                "salary_max": salary_max,
                                "salary_currency": salary_curr,
                                "posted_at": item.get("datePosted"),
                                "metadata": {"source_type": "JSON-LD"}
                            })
                except json.JSONDecodeError:
                    continue
            return jobs
        except httpx.HTTPError as he:
            raise NetworkError(f"JSON-LD fetch error: {he}")

    # --- DOM SCRAPING via Playwright ---
    def _discover_dom_selectors(self, url: str, company_name: str, parser_config: Dict[str, Any], limit: int, page_num: int) -> List[Dict[str, Any]]:
        return run_async(self._discover_dom_selectors_async(url, company_name, parser_config, limit, page_num))

    async def _discover_dom_selectors_async(self, url: str, company_name: str, parser_config: Dict[str, Any], limit: int, page_num: int) -> List[Dict[str, Any]]:
        from playwright.async_api import async_playwright

        card_selector = parser_config.get("job_card_selector", ".job-card")
        link_selector = parser_config.get("job_link_selector", "a.job-link")
        title_selector = parser_config.get("job_title_selector", ".job-title")
        company_selector = parser_config.get("company_selector", ".job-company")
        location_selector = parser_config.get("location_selector", ".job-location")
        desc_selector = parser_config.get("description_selector", ".job-description")
        salary_selector = parser_config.get("salary_selector", ".job-salary")
        exp_selector = parser_config.get("experience_selector", ".job-experience")
        next_page_selector = parser_config.get("next_page_selector", "a.next-page")

        delay = float(parser_config.get("delay_between_requests", 1.0))

        discovered_jobs = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            current_url = url
            for p_idx in range(1, page_num + 1):
                logger.info(f"Loading jobs page {p_idx}: {current_url}")
                try:
                    await page.goto(current_url, wait_until="networkidle")
                except Exception as e:
                    await browser.close()
                    raise NetworkError(f"Failed to navigate to {current_url}: {e}")

                await asyncio.sleep(delay)

                if p_idx == page_num:
                    break

                next_el = page.locator(next_page_selector).first
                if await next_el.count() > 0:
                    href = await next_el.get_attribute("href")
                    if href:
                        current_url = urljoin(current_url, href)
                    else:
                        await next_el.click()
                        await page.wait_for_load_state("networkidle")
                        current_url = page.url
                else:
                    await browser.close()
                    return []

            cards = await page.locator(card_selector).all()
            logger.info(f"Found {len(cards)} job cards on page {page_num}")
            
            listings_to_fetch = []
            for idx, card in enumerate(cards[:limit]):
                title = ""
                company = company_name
                location = ""
                detail_url = ""

                try:
                    if title_selector:
                        title_el = card.locator(title_selector).first
                        if await title_el.count() > 0:
                            title = await title_el.inner_text()

                    if company_selector:
                        comp_el = card.locator(company_selector).first
                        if await comp_el.count() > 0:
                            company = await comp_el.inner_text()

                    if location_selector:
                        loc_el = card.locator(location_selector).first
                        if await loc_el.count() > 0:
                            location = await loc_el.inner_text()

                    if link_selector:
                        link_el = card.locator(link_selector).first
                        if await link_el.count() > 0:
                            href = await link_el.get_attribute("href")
                            if href:
                                detail_url = urljoin(page.url, href)
                except Exception as e:
                    logger.warning(f"Error extracting summary card indices: {e}")
                    continue

                if not title:
                    continue

                listings_to_fetch.append({
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": location.strip(),
                    "detail_url": detail_url
                })

            for item in listings_to_fetch:
                job_title = item["title"]
                job_company = item["company"]
                job_location = item["location"]
                detail_url = item["detail_url"]

                desc = ""
                salary_min = None
                salary_max = None
                exp_min = None

                if detail_url:
                    logger.info(f"Fetching job detail page: {detail_url}")
                    await asyncio.sleep(delay)
                    try:
                        await page.goto(detail_url, wait_until="networkidle")
                        
                        if desc_selector:
                            desc_el = page.locator(desc_selector).first
                            if await desc_el.count() > 0:
                                desc = await desc_el.inner_text()

                        if salary_selector:
                            sal_el = page.locator(salary_selector).first
                            if await sal_el.count() > 0:
                                sal_text = await sal_el.inner_text()
                                numbers = [float(n) for n in re.findall(r'\d+', sal_text.replace(',', ''))]
                                if len(numbers) >= 2:
                                    salary_min = numbers[0]
                                    salary_max = numbers[1]
                                elif len(numbers) == 1:
                                    salary_min = numbers[0]

                        if exp_selector:
                            exp_el = page.locator(exp_selector).first
                            if await exp_el.count() > 0:
                                exp_text = await exp_el.inner_text()
                                exp_nums = [float(n) for n in re.findall(r'\d+', exp_text)]
                                if exp_nums:
                                    exp_min = exp_nums[0]
                    except Exception as e:
                        logger.error(f"Error opening detail page {detail_url}: {e}")
                        desc = f"Failed to fetch detailed description. Link: {detail_url}"
                else:
                    detail_url = url
                    desc = f"Direct description not available. Postings listing: {url}"

                ext_id = f"dom-{abs(hash(f'{job_title}-{job_company}-{job_location}'))}"

                discovered_jobs.append({
                    "external_id": ext_id,
                    "title": job_title,
                    "company": job_company,
                    "location": job_location,
                    "description": desc.strip(),
                    "job_url": detail_url,
                    "application_url": detail_url,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "experience_min": exp_min,
                    "metadata": {"source_type": "DOM Selector scraper"}
                })

            await browser.close()
            
        return discovered_jobs
