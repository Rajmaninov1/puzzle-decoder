import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, Dict, Any

import aiohttp
import orjson
import structlog

try:
    import uvloop  # noqa
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass  # uvloop is not essential, but preferred


class HTTPClientManager:
    """Optimized HTTP session singleton."""
    _instance: Optional['HTTPClientManager'] = None
    _session: Optional[aiohttp.ClientSession] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> 'HTTPClientManager':
        """Singleton instance creation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.logger = structlog.get_logger()
        return cls._instance

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create a session with double-checked locking."""
        # Hot path: quick check without locking
        if self._session and not self._session.closed:
            return self._session

        # Slow path: lock for creation
        async with self._lock:
            if self._session is None or self._session.closed:
                self.logger.debug("Creating new HTTP session")
                self._session = await self._create_session()
        return self._session

    @staticmethod
    async def _create_session() -> aiohttp.ClientSession:
        """Create an HTTP session with performance config."""
        connector = HTTPClientManager._create_connector()
        timeout = HTTPClientManager._create_timeout()
        headers = HTTPClientManager._create_headers()
        
        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            json_serialize=lambda x: orjson.dumps(x).decode('utf-8'),
            raise_for_status=False,
        )

    @staticmethod
    def _create_connector() -> aiohttp.TCPConnector:
        """Create an optimized TCP connector."""
        return aiohttp.TCPConnector(
            limit=0,  # No total limit
            limit_per_host=0,  # No limit per host
            ttl_dns_cache=600,  # DNS cache for 10 minutes
            use_dns_cache=True,
            keepalive_timeout=60,  # Reuse connections
            force_close=False,  # Aggressively reuse connections
        )

    @staticmethod
    def _create_timeout() -> aiohttp.ClientTimeout:
        """Create timeout configuration."""
        return aiohttp.ClientTimeout(
            total=10,
            connect=2,
            sock_read=8
        )

    @staticmethod
    def _create_headers() -> Dict[str, str]:
        """Create default headers."""
        return {
            'User-Agent': 'PuzzleSolver/2.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        }

    async def close(self) -> None:
        """Close the HTTP session and cleanup sockets."""
        if self._session and not self._session.closed:
            try:
                self.logger.debug("Closing HTTP session")
                await self._session.close()
                await asyncio.sleep(0.25)
            except Exception as e:
                self.logger.error("Error closing HTTP session", error=str(e))

    @asynccontextmanager
    async def request(self, method: str, url: str, **kwargs) -> AsyncGenerator[aiohttp.ClientResponse, None]:
        """HTTP request context manager."""
        try:
            session = await self.get_session()
            async with session.request(method, url, **kwargs) as response:
                yield response
        except aiohttp.ClientConnectionError as e:
            self.logger.error("Connection error", url=url, method=method, error=str(e))
            raise
        except asyncio.TimeoutError as e:
            self.logger.error("Request timeout", url=url, method=method, error=str(e))
            raise
        except Exception as e:
            self.logger.error("Unexpected request error", url=url, method=method, error=str(e))
            raise

    async def fetch_json(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Optimized JSON fetch helper."""
        try:
            async with self.request('GET', url, **kwargs) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return orjson.loads(data)
                elif resp.status >= 400:
                    self.logger.warning("HTTP error response", url=url, status=resp.status)
                else:
                    self.logger.debug("Non-success HTTP status", url=url, status=resp.status)
        except aiohttp.ClientConnectionError as e:
            self.logger.error("Connection failed", url=url, error=str(e))
        except asyncio.TimeoutError as e:
            self.logger.error("Request timed out", url=url, error=str(e))
        except orjson.JSONDecodeError as e:
            self.logger.error("JSON decode failed", url=url, error=str(e))
        except (ValueError, TypeError, RuntimeError) as e:
            self.logger.error("Unexpected error in fetch_json", url=url, error=str(e))
        return None


# Singleton instance
http_manager = HTTPClientManager()


async def get_http_session() -> aiohttp.ClientSession:
    """Get a global HTTP session."""
    return await http_manager.get_session()


async def close_http_session() -> None:
    """Close a global HTTP session."""
    await http_manager.close()
