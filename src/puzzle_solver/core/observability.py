from contextvars import ContextVar

from opentelemetry import trace
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Context variables for request tracing
correlation_id: ContextVar[str] = ContextVar('correlation_id', default='')

# OpenTelemetry tracer
tracer = trace.get_tracer(__name__)

# Prometheus metrics
request_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
circuit_breaker_state = Counter('circuit_breaker_state_changes_total', 'Circuit breaker state changes',
                                ['service', 'state'])
service_discovery_operations = Counter('service_discovery_operations_total', 'Service discovery operations',
                                       ['operation'])
fragment_counter = Counter('fragments_total', 'Fragment processing', ['status'])


def get_metrics():
    """Get Prometheus metrics."""
    return generate_latest()


# Export content type
__all__ = ['correlation_id', 'tracer', 'fragment_counter', 'request_counter', 'request_duration',
           'circuit_breaker_state', 'service_discovery_operations', 'get_metrics', 'CONTENT_TYPE_LATEST']
