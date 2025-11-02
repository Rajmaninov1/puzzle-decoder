"""
Assumptions:
- Fragment server responds with JSON containing id, index, and text fields
- Fragment indices start from 0 and are consecutive
- Server has random delays between 100-400ms per request
- Total fragments are bounded but unknown count
- Same ID always returns same fragment
- Puzzle completion requires all fragments in sequence
- Maximum concurrency improves performance without overwhelming server
[Lumu Challenge]
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from puzzle_solver.api.middleware import observability_middleware
from puzzle_solver.api.routers import health, observability, auth
from puzzle_solver.api.v1.routers import puzzle as puzzle_v1
from puzzle_solver.config.settings import settings
from puzzle_solver.core.logging_config import setup_logging


def setup_tracing():
    """Configure OpenTelemetry tracing with OTLP."""
    from opentelemetry.sdk.resources import Resource

    try:
        import importlib.metadata
        version = importlib.metadata.version("puzzle-decoder")
    except Exception:
        version = "1.0.0"

    resource = Resource.create({
        "service.name": "puzzle-solver",
        "service.version": version
    })

    trace.set_tracer_provider(TracerProvider(resource=resource))
    otlp_exporter = OTLPSpanExporter(
        endpoint=f"http://{getattr(settings, 'JAEGER_HOST', 'localhost')}:4317",
        insecure=True
    )
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    # Startup
    setup_logging()
    setup_tracing()
    FastAPIInstrumentor.instrument_app(app)
    yield
    # Shutdown
    FastAPIInstrumentor.uninstrument_app(app)


app = FastAPI(
    title="Puzzle Solver API",
    description="High-performance puzzle solving service with API versioning",
    version="1.0.0",
    lifespan=lifespan
)

app.middleware("http")(observability_middleware)

# Health and observability (unversioned)
app.include_router(health.router)
app.include_router(observability.router)
app.include_router(auth.router)

# V1 API routes
app.include_router(puzzle_v1.router, prefix="/v1")
