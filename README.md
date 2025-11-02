# Puzzle Decoder

A high-performance Python application that solves puzzles by fetching and assembling text fragments from a remote service with maximum concurrency and sub-second execution times.

___

## Author

Julian Tolosa 
GitHub: [@Rajmaninov1](https://github.com/Rajmaninov1)

___

## How to Run

___

### Configuration
Copy `.env.example` to `.env` and adjust settings:
```bash
cp .env.example .env
# Edit .env with your fragment service URL and performance settings
```

___

### Local execution

#### Prerequisites
- Python 3.12+ 
- [uv](https://docs.astral.sh/uv/) package manager

```bash
# Clone the repository
git clone https://github.com/Rajmaninov1/puzzle-decoder
cd puzzle-decoder

# Install dependencies
uv sync
```

#### CLI Mode
```bash
# Run the puzzle solver (multiple methods available)
# Method 1: Python module
uv run python -m puzzle_solver.cli.main

# Method 2: Script entry point
uv run puzzle-solver

# Method 3: Direct execution
uv run python src/puzzle_solver/cli/main.py
```

#### FastAPI Web Server
```bash
# Start the FastAPI server
uv run fastapi dev src/puzzle_solver/api/main.py

# Alternative with uvicorn directly
uv run uvicorn puzzle_solver.api.main:app --reload --host 0.0.0.0 --port 8000

# Access the API
# - Swagger UI: http://localhost:8000/docs
# - ReDoc: http://localhost:8000/redoc
# - Health check: http://localhost:8000/health
```

___

### Docker

#### Prerequisites
- Docker

```bash
# Build the image
docker build -t puzzle-solver .
```

#### CLI Mode
```bash
# Method 1: CLI execution only
docker run --rm --env-file .env puzzle-solver python -m puzzle_solver.cli.main

# Method 2: CLI with puzzle server
docker-compose run --rm puzzle-solver python -m puzzle_solver.cli.main
```

#### FastAPI Web Server
```bash
# Method 1: FastAPI web server only
docker run --rm --env-file .env -p 8000:8000 puzzle-solver
# Then visit: http://localhost:8000/docs

# Method 2: Docker Compose with puzzle server
docker-compose up
# Then visit: http://localhost:8000/docs
```

___

## API Features

### API Versioning
- **URL-based versioning**: `/v1/puzzle/solve`
- **Header-based versioning**: `Accept: application/vnd.api+json;version=1`
- **Custom header**: `API-Version: v1`
- **Automatic fallback** to v1 for unspecified versions

### Authentication & Security
```bash
# Get JWT token
curl -X POST http://localhost:8000/auth/token \
  -u admin:secret123

# Use token for protected endpoints
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/v1/puzzle/solve
```

#### Testing Authentication in Swagger UI

1. **Start the API server**:
   ```bash
   uv run fastapi dev src/puzzle_solver/api/main.py
   ```

2. **Open Swagger UI**: Navigate to http://localhost:8000/docs

3. **Get JWT Token**:
   - Find the `POST /auth/token` endpoint
   - Click "Try it out"
   - Click "Execute" (uses default credentials: admin/secret123)
   - Copy the `access_token` from the response

4. **Authorize in Swagger**:
   - Click the "Authorize" button (🔒) at the top right
   - In the "HTTPBearer" field, paste your token generated in the last step
   - Click "Authorize" then "Close"

5. **Test Protected Endpoint**:
   - Find the `GET /v1/puzzle/solve` endpoint
   - Click "Try it out" then "Execute"
   - Should return the puzzle solution with your username

6. **Test Without Token**:
   - Click "Authorize" → "Logout" to clear the token
   - Try the puzzle endpoint again → Should get 401 Unauthorized

### Health & Observability
```bash
# Health check (liveness probe)
curl http://localhost:8000/health

# Readiness check (external connectivity)
curl http://localhost:8000/ready

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Request Tracing
- **Correlation IDs**: Automatic generation or custom via `X-Correlation-ID` header
- **Distributed tracing**: OpenTelemetry integration
- **Structured logging**: JSON format with correlation tracking

___

## 🚀 Performance Results

```
2025-11-01T23:47:26.705129Z [info     ] Fragment discovery completed   completion_rate=100.0% correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e missing_count=0 total_found=28
2025-11-01T23:47:26.705369Z [info     ] Assembling puzzle text         correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e fragment_count=28
2025-11-01T23:47:26.705637Z [info     ] Puzzle solved successfully     completion_rate=100.0% correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e elapsed=0.514s
2025-11-01T23:47:26.705877Z [info     ] ============================================================ correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.706096Z [info     ] hello world quick brown fox jumps over lazy dog you have to call all request at same time if you want to see the puzzle fragments fast enough correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.706291Z [info     ] ============================================================ correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.706461Z [info     ] Tiempo: 0.514s | Fragmentos: 28 correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.706662Z [info     ] Velocidad: 54.4 fragments/s    correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.706783Z [info     ] Requests exitosos: 40          correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.706876Z [info     ] Completitud: 100.0% (100.0%)   correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.706980Z [info     ] Fragmentos faltantes: 0        correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.707061Z [info     ] Status: Complete               correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.707143Z [info     ] ============================================================ correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
2025-11-01T23:47:26.707242Z [info     ] Less than one second! :D       correlation_id=6d5c7734-d77e-4d81-9000-a6b30abfdd0e
```

### ✨ Bonus Achievement

**Sub-second execution achieved!** The puzzle solver completes in **0.514 seconds**, well under the 1-second bonus requirement.

___

## Strategy for Speed and Correctness

### 🧠 Key settings for performance tuning:
- `FRAGMENT_SERVICE__MAX_CONCURRENT`: Parallel request limit (default: 40)
- `FRAGMENT_SERVICE__TIMEOUT`: Request timeout in seconds (default: 0.5)
- `FRAGMENT_SERVICE__INITIAL_BATCH_SIZE`: Discovery batch size (default: 10)

### 🚀 Speed Optimizations
- **Massive Concurrency**: Configurable parallel HTTP requests using aiohttp with unlimited connection pooling
- **Optimized Discovery**: Four concurrent range scans for fragment discovery of batch size (batch size * 4)
- **Fast JSON Processing**: orjson for high-performance JSON parsing
- **Connection Reuse**: Aggressive HTTP keep-alive and connection pooling with TCPConnector optimization
- **uvloop Integration**: Event loop optimization when available
- **Minimal Timeouts**: Configurable request timeout
- **Singleton HTTP Manager**: Shared session across all requests with double-checked locking
- **Batch Processing**: Parallel fragment fetching with asyncio.gather for maximum throughput

### ✅ Fragment Completion Strategies
- **Gap Detection**: Automatic identification of missing indices between min/max fragment range
- **Continuous Search Loop**: Iterative missing fragment discovery until 100% completion
- **Duplicate Elimination**: Automatic deduplication by fragment index to prevent duplicates
- **Range Boundary Analysis**: Dynamic detection of fragment sequence boundaries (check min/max fragment index)
- **Missing Index Tracking**: Real-time monitoring of incomplete fragment sequences
- **Completion Validation**: Ensures no gaps exist in the final fragment sequence

### ✅ Correctness Guarantees
- **Pydantic Models**: Type-safe data structures with automatic validation
- **Structured Validation**: Fragment data integrity checks at parse time
- **Retry Logic**: Tenacity-based retries for network failures with exponential backoff
- **Comprehensive Logging**: Structured logging with correlation IDs for request tracing
- **Error Isolation**: Handling of partial failures without stopping fragment discovery
- **Observability**: OpenTelemetry tracing and Prometheus metrics for monitoring
- **Authentication**: JWT-based security for API endpoints with proper token validation

___

### 🧠 Architecture
```
┌─────────────────┐ ┌─────────────────┐
│   CLI Layer     │ │  FastAPI Layer  │
└─────────────────┘ └─────────────────┘
         │                  │
         └────────┬─────────┘
                  ▼
        ┌──────────────────┐    ┌─────────────────┐
        │  Puzzle Service  │───▶│Fragment Service │
        └──────────────────┘    └─────────────────┘
                 │                       │
                 ▼                       ▼
        ┌──────────────────┐    ┌────────────────┐
        │  Text Assembly   │    │   HTTP Client  │
        └──────────────────┘    └────────────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │ Puzzle Server   │
                                │ (External API)  │
                                └─────────────────┘
```

### 🧠 Middleware Stack
```
Request → Observability Middleware → API Versioning → Authentication → Route Handler
    ↓           ↓                        ↓               ↓
Correlation  Metrics &              Version         JWT Token
   ID        Tracing               Validation      Verification
```

___

## 🧠 Project Structure

```
puzzle decoder/
├── .github/ 
│   └── workflows/ # CI/CD automation
│   │   └── ci.yml
├── scripts/ # Utility scripts and tools
│   ├── __init__.py
│   ├── folder_structure.txt
│   ├── project_structure.py
│   └── puzzle_fragmen_endpoint_test.py
├── src/ 
│   ├── puzzle_solver/ 
│   │   ├── api/ # FastAPI web interface
│   │   │   ├── routers/ 
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── health.py
│   │   │   │   └── observability.py
│   │   │   ├── v1/ 
│   │   │   │   ├── routers/ 
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── puzzle.py
│   │   │   │   └── __init__.py
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── main.py
│   │   │   ├── middleware.py
│   │   │   ├── models.py
│   │   │   └── versioning.py
│   │   ├── cli/ # Command-line interface
│   │   │   ├── __init__.py
│   │   │   └── main.py
│   │   ├── clients/ # HTTP client management
│   │   │   ├── __init__.py
│   │   │   └── http_client.py
│   │   ├── config/ # Configuration and settings
│   │   │   ├── __init__.py
│   │   │   └── settings.py
│   │   ├── core/ # Logging and core utilities
│   │   │   ├── __init__.py
│   │   │   ├── logging_config.py
│   │   │   └── observability.py
│   │   ├── domain/ 
│   │   │   ├── models/ # Data models (Fragment, FragmentBatch)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── fragment.py
│   │   │   │   └── puzzle.py
│   │   │   ├── services/ # Business logic (PuzzleService, FragmentService)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── fragment.py
│   │   │   │   └── puzzle.py
│   │   │   └── __init__.py
│   │   ├── utils/ # Utility functions
│   │   │   ├── __init__.py
│   │   │   └── fragment_utils.py
│   │   └── __init__.py
│   └── __init__.py
├── tests/ 
│   ├── unit/ # Unit tests
│   │   ├── __init__.py
│   │   ├── test_fragment_service.py
│   │   ├── test_fragment_utils.py
│   │   └── test_puzzle_service.py
│   ├── __init__.py
│   └── conftest.py
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
└── uv.lock
```

## Testing

```bash
# Run all tests
uv run pytest

# Run specific test files
uv run pytest tests/unit/test_puzzle_service.py -v
```

## 🧼 Code Quality

```bash
# Run linting
uv run ruff check src/ tests/

# Run formatting check
uv run ruff format --check src/ tests/

# Auto-fix linting issues
uv run ruff check --fix src/ tests/

# Auto-format code
uv run ruff format src/ tests/
```

___

## 🧠 Monitoring

The application provides structured logging with:
- Request/response timing
- Success/failure rates  
- Fragment discovery progress
- Error details with context

Set `LOG_LEVEL=DEBUG` for detailed performance insights.

___
