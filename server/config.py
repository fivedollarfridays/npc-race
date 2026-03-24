"""Server configuration."""

from dataclasses import dataclass, field


@dataclass
class Settings:
    host: str = "0.0.0.0"
    port: int = 8000
    db_path: str = "data/npcrace.db"
    cors_origins: list[str] = field(
        default_factory=lambda: [
            "http://localhost:8000",
            "http://localhost:3000",
            "http://127.0.0.1:8000",
        ]
    )
    static_dir: str = "server/static"
    viewer_dir: str = "viewer"


settings = Settings()
