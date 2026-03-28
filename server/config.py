"""Server configuration."""

import os
from dataclasses import dataclass, field

_DEFAULT_ORIGINS = (
    "http://localhost:8000,http://localhost:3000,http://127.0.0.1:8000,"
    "https://agentgrounds.ai,https://www.agentgrounds.ai"
)


@dataclass
class Settings:
    host: str = "0.0.0.0"
    port: int = 8000
    db_path: str = "data/npcrace.db"
    cors_origins: list[str] = field(
        default_factory=lambda: os.environ.get(
            "CORS_ORIGINS", _DEFAULT_ORIGINS
        ).split(",")
    )
    static_dir: str = "server/static"
    viewer_dir: str = "viewer"


settings = Settings()
