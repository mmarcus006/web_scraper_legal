"""Async API client with retry logic and connection pooling."""

import asyncio
import random
from datetime import datetime
from typing import Optional, List, Dict, Any

import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .models import Opinion, APIResponse
from .config import settings
from .utils import get_logger


logger = get_logger(__name__)


class APIClient:
    """Async API client for Dawson Court API."""
    
    def __init__(self, max_concurrent: int = 10):
        """Initialize API client."""
        self.base_url = settings.api_base_url
        self.headers = settings.headers
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(
            calls=10,
            period=1.0,
            max_burst=20
        )
    
    async def __aenter__(self):
        """Enter async context."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        await self.close()
    
    async def start(self):
        """Start the API client session."""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=self.max_concurrent,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
            )
            
            timeout = aiohttp.ClientTimeout(
                total=settings.api_timeout * 3,
                connect=10,
                sock_read=settings.api_timeout,
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers,
                trust_env=True,
            )
            
            logger.info(f"API client started with {self.max_concurrent} max concurrent connections")
    
    async def close(self):
        """Close the API client session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("API client closed")
    
    def _log_retry(self, retry_state):
        """Log retry attempts."""
        logger.warning(
            f"Retry attempt {retry_state.attempt_number} for {retry_state.fn.__name__} "
            f"after {retry_state.outcome.exception()}"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        after=lambda retry_state: logger.warning(f"Retry {retry_state.attempt_number}")
    )
    async def _make_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        **kwargs
    ) -> APIResponse:
        """Make HTTP request with retry logic."""
        async with self.semaphore:
            await self._rate_limiter.acquire()
            
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    **kwargs
                ) as response:
                    data = None
                    if response.content_type == "application/json":
                        data = await response.json()
                    else:
                        data = await response.text()
                    
                    return APIResponse(
                        success=response.status < 400,
                        data=data,
                        status_code=response.status,
                        headers=dict(response.headers),
                        error=None if response.status < 400 else f"HTTP {response.status}",
                    )
                    
            except asyncio.TimeoutError as e:
                logger.error(f"Request timeout for {url}: {e}")
                return APIResponse(success=False, error=f"Timeout: {e}")
            except aiohttp.ClientError as e:
                logger.error(f"Client error for {url}: {e}")
                return APIResponse(success=False, error=f"Client error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                return APIResponse(success=False, error=f"Unexpected error: {e}")
    
    async def fetch_opinions(
        self,
        start_date: datetime,
        end_date: datetime,
        opinion_types: str = "MOP,SOP,OST,TCOP"
    ) -> List[Opinion]:
        """Fetch opinions for a date range."""
        start_str = f"{start_date.month}/{start_date.day}/{start_date.year}"
        end_str = f"{end_date.month}/{end_date.day}/{end_date.year}"
        
        params = {
            "dateRange": "customDates",
            "startDate": start_str,
            "endDate": end_str,
            "opinionTypes": opinion_types,
        }
        
        url = f"{self.base_url}/opinion-search"
        logger.info(f"Fetching opinions: {start_str} to {end_str}")
        
        response = await self._make_request("GET", url, params=params)
        
        if response.success and response.data:
            # Handle both list and dict responses
            if isinstance(response.data, list):
                opinions_data = response.data
            elif isinstance(response.data, dict) and "opinions" in response.data:
                opinions_data = response.data["opinions"]
            else:
                opinions_data = []
            
            opinions = []
            for item in opinions_data:
                try:
                    opinion = Opinion(**item)
                    opinions.append(opinion)
                except Exception as e:
                    logger.error(f"Failed to parse opinion: {e}, data: {item}")
            
            logger.info(f"Found {len(opinions)} opinions for {start_str} to {end_str}")
            return opinions
        else:
            logger.error(f"Failed to fetch opinions: {response.error}")
            return []
    
    async def get_document_url(
        self,
        docket_number: str,
        docket_entry_id: str
    ) -> Optional[str]:
        """Get download URL for a document."""
        url = f"{self.base_url}/{docket_number}/{docket_entry_id}/public-document-download-url"
        
        response = await self._make_request("GET", url)
        
        if response.success and response.data:
            # Response can be a dict with 'url' key or direct string
            if isinstance(response.data, dict) and "url" in response.data:
                return response.data["url"]
            elif isinstance(response.data, str):
                return response.data
        
        logger.error(f"Failed to get document URL for {docket_number}: {response.error}")
        return None
    
    async def download_file(
        self,
        url: str,
        chunk_size: int = 8192,
        progress_callback: Optional[callable] = None
    ) -> bytes:
        """Download file from URL."""
        async with self.semaphore:
            await self._rate_limiter.acquire()
            
            try:
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get("Content-Length", 0))
                    chunks = []
                    downloaded = 0
                    
                    async for chunk in response.content.iter_chunked(chunk_size):
                        chunks.append(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            await progress_callback(downloaded, total_size)
                    
                    return b"".join(chunks)
                    
            except Exception as e:
                logger.error(f"Failed to download file from {url}: {e}")
                raise


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, calls: int, period: float, max_burst: int = None):
        """
        Initialize rate limiter.
        
        Args:
            calls: Number of calls allowed per period
            period: Time period in seconds
            max_burst: Maximum burst size (defaults to calls)
        """
        self.calls = calls
        self.period = period
        self.max_burst = max_burst or calls
        self.tokens = self.max_burst
        self.last_update = asyncio.get_event_loop().time()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary."""
        async with self.lock:
            while self.tokens <= 0:
                now = asyncio.get_event_loop().time()
                elapsed = now - self.last_update
                
                # Refill tokens based on elapsed time
                tokens_to_add = elapsed * (self.calls / self.period)
                self.tokens = min(self.max_burst, self.tokens + tokens_to_add)
                self.last_update = now
                
                if self.tokens <= 0:
                    # Wait for next token
                    wait_time = (1 - self.tokens) * (self.period / self.calls)
                    wait_time = max(0.01, wait_time)  # Minimum wait
                    await asyncio.sleep(wait_time)
            
            self.tokens -= 1