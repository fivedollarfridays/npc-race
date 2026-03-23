"""Launch the race replay viewer in a browser.

Copies replay.json into the viewer directory, starts a local HTTP server
on a free port, and opens the browser to dashboard.html.
"""

import functools
import http.server
import os
import shutil
import socketserver
import webbrowser

_PORT = 8765


def _find_viewer_dir() -> str:
    """Return the absolute path to the viewer/ directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__)))


def _prepare_viewer(replay_path: str, viewer_dir: str) -> str | None:
    """Copy replay into viewer dir, return URL to open. None on failure."""
    if not os.path.isdir(viewer_dir):
        print("viewer/ directory not found")
        return None

    shutil.copy2(
        os.path.abspath(replay_path),
        os.path.join(viewer_dir, "replay.json"),
    )

    url = f"http://localhost:{_PORT}/dashboard.html"
    return url


def launch_viewer(replay_path: str) -> None:
    """Copy replay into viewer dir, start HTTP server, and open browser.

    Silently returns when running under pytest (PYTEST_CURRENT_TEST env var)
    or when the viewer directory does not exist.
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return

    viewer_dir = _find_viewer_dir()
    url = _prepare_viewer(replay_path, viewer_dir)
    if url is None:
        return

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=viewer_dir,
    )

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", _PORT), handler) as httpd:
        print(f"\nViewer: {url}  (Ctrl-C to stop)")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nViewer stopped.")
