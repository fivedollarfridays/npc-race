"""Tests for deployment configuration files."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_dockerfile_exists():
    """Dockerfile must exist at project root."""
    assert (ROOT / "Dockerfile").is_file()


def test_dockerfile_uses_python_313_slim():
    """Dockerfile should use python:3.13-slim base image."""
    text = (ROOT / "Dockerfile").read_text()
    assert "python:3.13-slim" in text


def test_dockerfile_exposes_8000():
    """Dockerfile should expose port 8000."""
    text = (ROOT / "Dockerfile").read_text()
    assert "EXPOSE 8000" in text


def test_dockerfile_runs_uvicorn():
    """Dockerfile CMD should run uvicorn with server.app:app."""
    text = (ROOT / "Dockerfile").read_text()
    assert "uvicorn" in text
    assert "server.app:app" in text


def test_dockerfile_installs_server_extras():
    """Dockerfile should install the [server] extras."""
    text = (ROOT / "Dockerfile").read_text()
    assert "[server]" in text


# --- Procfile ---


def test_procfile_exists():
    """Procfile must exist at project root."""
    assert (ROOT / "Procfile").is_file()


def test_procfile_runs_uvicorn():
    """Procfile web process should run uvicorn with server.app:app."""
    text = (ROOT / "Procfile").read_text()
    assert text.startswith("web:")
    assert "uvicorn" in text
    assert "server.app:app" in text


def test_procfile_uses_port_env_var():
    """Procfile should reference $PORT for Railway/Heroku compatibility."""
    text = (ROOT / "Procfile").read_text()
    assert "PORT" in text


# --- CORS config ---


def test_cors_origins_reads_from_env(monkeypatch):
    """Settings.cors_origins should respect CORS_ORIGINS env var."""
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com,https://other.com")
    # Re-import to pick up new env
    from server.config import Settings

    s = Settings()
    assert s.cors_origins == ["https://example.com", "https://other.com"]


def test_cors_default_includes_agentgrounds():
    """Default CORS origins should include agentgrounds.ai."""
    from server.config import Settings

    s = Settings()
    origins = s.cors_origins
    assert any("agentgrounds.ai" in o for o in origins)


# --- Deployment docs ---


def test_deployment_docs_exist():
    """Deployment documentation must exist."""
    assert (ROOT / "docs" / "deployment.md").is_file()
