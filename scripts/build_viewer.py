"""Build viewer.html by inlining JS modules into a single self-contained file.

Usage:
    python scripts/build_viewer.py

Reads viewer/viewer.html (shell with <script src="path"> tags),
replaces each external script tag with the referenced JS file wrapped in
inline <script> tags, and writes the result to viewer.html at the project root.
"""
import re
import sys
from pathlib import Path


def _resolve_script_src(match: re.Match, viewer_dir: Path) -> str:
    """Replace a <script src="..."> tag with inlined script content."""
    path = match.group(1).strip()
    js_path = viewer_dir / path
    if not js_path.exists():
        print(f"ERROR: {js_path} not found", file=sys.stderr)
        sys.exit(1)
    content = js_path.read_text()
    return f"<script>\n{content}</script>"


def build() -> Path:
    """Build viewer.html by inlining all JS modules.

    Returns the path to the built file.
    """
    viewer_dir = Path(__file__).resolve().parent.parent / "viewer"
    shell = (viewer_dir / "viewer.html").read_text()

    result = re.sub(
        r'<script src="([^"]+)"></script>',
        lambda m: _resolve_script_src(m, viewer_dir),
        shell,
    )

    out_path = Path(__file__).resolve().parent.parent / "viewer.html"
    out_path.write_text(result)
    print(f"Built {out_path} ({len(result)} bytes)")
    return out_path


if __name__ == "__main__":
    build()
