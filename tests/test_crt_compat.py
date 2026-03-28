"""Tests for CRT-compatible game UI (T48.4)."""

from pathlib import Path


EDITOR_HTML = Path("server/static/editor.html")
INDEX_HTML = Path("server/static/index.html")


class TestEditorEmbedDetection:
    """Editor.html must detect when running inside an iframe."""

    def test_editor_has_embedded_class_logic(self) -> None:
        html = EDITOR_HTML.read_text()
        assert "embedded" in html, "editor.html must reference 'embedded' CSS class"

    def test_editor_detects_iframe(self) -> None:
        html = EDITOR_HTML.read_text()
        assert "window.top" in html or "window.parent" in html, (
            "editor.html must detect iframe embedding via window.top or window.parent"
        )

    def test_editor_supports_embed_query_param(self) -> None:
        html = EDITOR_HTML.read_text()
        assert "embed" in html, (
            "editor.html must support ?embed=true query parameter"
        )


class TestEditorDarkTheme:
    """Editor must have dark theme suitable for CRT monitor frame."""

    def test_background_is_dark(self) -> None:
        html = EDITOR_HTML.read_text()
        assert "#0a0a0f" in html, "background must be dark (#0a0a0f)"

    def test_no_white_background(self) -> None:
        html = EDITOR_HTML.read_text()
        # Ensure no explicit white backgrounds that would break CRT look
        assert "background: #fff" not in html
        assert "background: white" not in html
        assert "background:#fff" not in html


class TestEmbeddedCSS:
    """Embedded mode CSS must constrain layout for 800x600 CRT frame."""

    def test_embedded_removes_margin(self) -> None:
        html = EDITOR_HTML.read_text()
        assert "body.embedded" in html, (
            "editor.html must have body.embedded CSS rules"
        )

    def test_embedded_hides_hero_or_header(self) -> None:
        """In embedded mode, non-essential chrome should be hidden."""
        html = EDITOR_HTML.read_text()
        # Either hide header or hero section in embedded mode
        assert "embedded" in html and "display: none" in html


class TestCORSConfig:
    """CORS must allow agentgrounds.ai origins."""

    def test_default_origins_include_agentgrounds(self) -> None:
        from server.config import _DEFAULT_ORIGINS

        assert "https://agentgrounds.ai" in _DEFAULT_ORIGINS
        assert "https://www.agentgrounds.ai" in _DEFAULT_ORIGINS


class TestGameFrameEndpoint:
    """A /api/game-frame endpoint must exist for embedding."""

    def test_game_frame_route_registered(self) -> None:
        from server.app import app

        route_paths = [r.path for r in app.routes]
        assert "/api/game-frame" in route_paths
