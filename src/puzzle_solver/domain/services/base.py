import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

import structlog
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from puzzle_solver.clients.http_client import http_manager

T = TypeVar("T", bound=BaseModel)


class BaseWebService(ABC, Generic[T]):
    """Base web service with concurrent requests and retries."""

    def __init__(
        self, base_url: str, max_concurrent: int = 100, timeout: float = 5.0, max_retries: int = 3
    ) -> None:  # Initialize base web service with concurrency and retry configuration !!!
        self.base_url = base_url.rstrip("/")
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = structlog.get_logger()
        self.successful_requests = 0

    @abstractmethod
    def parse_response(self, data: Dict[str, Any]) -> Optional[T]:  # Parse JSON response to model abstract method !!!
        pass

    @abstractmethod
    def build_url(self, **params: Any) -> str:  # Build service URL abstract method !!!
        pass

    async def fetch_single(
        self, **params: Any
    ) -> Optional[T]:  # Fetch single item with semaphore concurrency control !!!
        async with self.semaphore:
            return await self._fetch_with_retry(**params)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=2.0),
        retry=retry_if_exception_type((asyncio.TimeoutError, ConnectionError)),
    )
    async def _fetch_with_retry(
        self, **params: Any
    ) -> Optional[T]:  # Fetch with tenacity retry logic for network resilience !!!
        url = self.build_url(**params)
        self.logger.debug("Fetching URL", url=url)

        try:
            json_data = await http_manager.fetch_json(url)
            if json_data:
                self.successful_requests += 1
                self.logger.debug("Fetch successful", url=url)
                return self.parse_response(json_data)
            self.logger.debug("No data received", url=url)
            return None
        except (asyncio.TimeoutError, ConnectionError) as e:
            # guardrail: Handle retryable network errors gracefully
            self.logger.warning("Retryable error fetching", url=url, error=str(e))
            raise
        except Exception as e:
            # guardrail: Handle non-retryable errors without crashing
            self.logger.error("Non-retryable error fetching", url=url, error=str(e))
            return None

    async def fetch_batch(
        self, param_list: List[Dict[str, Any]]
    ) -> List[T]:  # Fetch multiple items in parallel with error handling !!!
        self.logger.debug("Starting batch fetch", batch_size=len(param_list))
        tasks = [self.fetch_single(**params) for params in param_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        filtered_results = self._filter_valid_results(results)
        self.logger.debug("Batch fetch completed", requested=len(param_list), successful=len(filtered_results))
        return filtered_results

    async def fetch_range(
        self, start: int, count: int, param_builder: Callable[[int], Dict[str, Any]]
    ) -> List[T]:  # Fetch range of items using parameter builder function !!!
        param_list = [param_builder(start + i) for i in range(count)]
        return await self.fetch_batch(param_list)

    def _filter_valid_results(
        self, results: List[Any]
    ) -> List[T]:  # Filter valid results from batch fetch excluding exceptions !!!
        valid_results: List[T] = []
        for result in results:
            if isinstance(result, BaseModel) and result is not None:
                valid_results.append(result)
            elif isinstance(result, Exception):
                self.logger.debug(f"Batch fetch exception: {result}")
        return valid_results
