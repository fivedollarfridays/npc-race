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

def _find_viewer_dir() -> str:
    """Return the absolute path to the viewer/ directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__)))


def _prepare_viewer(replay_path: str, viewer_dir: str, port: int) -> str | None:
    """Copy replay into viewer dir, return URL to open. None on failure."""
    if not os.path.isdir(viewer_dir):
        print("viewer/ directory not found")
        return None

    shutil.copy2(
        os.path.abspath(replay_path),
        os.path.join(viewer_dir, "replay.json"),
    )

    return f"http://localhost:{port}/dashboard.html"


def launch_viewer(replay_path: str) -> None:
    """Copy replay into viewer dir, start HTTP server, and open browser.

    Silently returns when PYTEST_CURRENT_TEST or CI env var is set,
    or when the viewer directory does not exist.
    """
    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI"):
        return

    viewer_dir = _find_viewer_dir()

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=viewer_dir,
    )

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", 0), handler) as httpd:
        port = httpd.server_address[1]
        url = _prepare_viewer(replay_path, viewer_dir, port)
        if url is None:
            return
        print(f"\nViewer: {url}  (Ctrl-C to stop)")
        webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nViewer stopped.")
