from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class FragmentServiceConfig(BaseModel):
    """Fragment service configuration."""
    base_url: str = Field(default="http://puzzle-server:8080", description="Fragment service host")
    endpoint: str = Field(default="/fragment", description="API endpoint path")
    max_concurrent: int = Field(default=40, description="Max parallel requests")
    timeout: float = Field(default=0.5, description="Request timeout in seconds")
    max_retries: int = Field(default=1, description="Retry attempts")
    initial_batch_size: int = Field(
        default=10, description="Batch size per range. Four parallel batches (initial_batch_size * 4)"
    )

    @property
    def full_url(self) -> str:
        """Full service URL."""
        if self.base_url.startswith(('http://', 'https://')):  # noqa
            return f"{self.base_url}{self.endpoint}"
        return f"https://{self.base_url}{self.endpoint}"


class PuzzleServiceConfig(BaseModel):
    """Puzzle service configuration."""
    stream_threshold: int = Field(default=100, description="Fragment count to trigger puzzle text by streaming")
    chunk_size: int = Field(
        default=50, description="Streaming chunk size in case puzzle message bigger than stream_threshold"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="console", description="Log format")
    colorize: bool = Field(default=True, description="Enable colored logs")
    timestamp_format: str = Field(default="iso", description="Timestamp format")
    include_stack_info: bool = Field(default=True, description="Include stack info")
    file_path: str | None = Field(default=None, description="Log file path")
    context_class: str = Field(default="dict", description="Context class")


class Settings(BaseSettings):
    """Application settings."""
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    fragment_service: FragmentServiceConfig = Field(default_factory=FragmentServiceConfig)
    puzzle_service: PuzzleServiceConfig = Field(default_factory=PuzzleServiceConfig)

    # JWT configuration
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_HOURS: int = Field(default=24, description="Token expiration hours")

    # OpenTelemetry configuration
    JAEGER_HOST: str = Field(default="localhost", description="Jaeger host")

    # Backward compatibility properties
    @property
    def LOG_LEVEL(self) -> str:
        return self.logging.level

    @property
    def LOG_FORMAT(self) -> str:
        return self.logging.format

    @property
    def LOG_COLORIZE(self) -> bool:
        return self.logging.colorize

    @property
    def LOG_TIMESTAMP_FORMAT(self) -> str:
        return self.logging.timestamp_format

    @property
    def LOG_INCLUDE_STACK_INFO(self) -> bool:
        return self.logging.include_stack_info

    @property
    def LOG_FILE_PATH(self) -> str | None:
        return self.logging.file_path

    @property
    def LOG_CONTEXT_CLASS(self) -> str:
        return self.logging.context_class

    @property
    def FRAGMENT_SERVICE(self) -> FragmentServiceConfig:
        return self.fragment_service

    @property
    def PUZZLE_SERVICE(self) -> PuzzleServiceConfig:
        return self.puzzle_service

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        env_file_encoding = "utf-8"
        extra = "allow"


settings = Settings()
