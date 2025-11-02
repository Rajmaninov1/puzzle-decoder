from fastapi import HTTPException, Request


def get_api_version(request: Request) -> str:
    """Extract an API version from URL path or headers."""
    # Check URL path first (/v1/, /v2/, etc.)
    path_parts = request.url.path.strip("/").split("/")
    if path_parts and path_parts[0].startswith("v") and path_parts[0][1:].isdigit():
        return path_parts[0]

    # Check Accept header (application/vnd.api+json;version=1)
    accept_header = request.headers.get("accept", "")
    if "version=" in accept_header:
        try:
            version_part = accept_header.split("version=")[1].split(";")[0].split(",")[0]
            return f"v{version_part}"
        except (IndexError, ValueError):
            pass

    # Check custom API-Version header
    api_version = request.headers.get("api-version")
    if api_version:
        return f"v{api_version}" if not api_version.startswith("v") else api_version

    # Default to v1
    return "v1"


def validate_version(version: str) -> str:
    """Validate and normalize API version."""
    supported_versions = ["v1"]
    if version not in supported_versions:
        raise HTTPException(
            status_code=400, detail=f"Unsupported API version: {version}. Supported: {supported_versions}"
        )
    return version
