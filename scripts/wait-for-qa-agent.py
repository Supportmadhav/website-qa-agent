from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / ".qa-agent" / "logs"

BACKEND_URL = "http://127.0.0.1:8000/api/health"
FRONTEND_URL = "http://127.0.0.1:5173"

TIMEOUT_SECONDS = 45


def url_ready(url: str) -> bool:
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Website-QA-Agent-Launcher",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=2,
        ) as response:
            return 200 <= response.status < 500

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
    ):
        return False


def show_log(
    filename: str,
    title: str,
) -> None:
    path = LOG_DIR / filename

    print()
    print("-" * 60)
    print(title)
    print("-" * 60)

    if not path.exists():
        print("No log file was created.")
        return

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()

    except OSError as exc:
        print(f"Could not read log: {exc}")
        return

    if not lines:
        print("Log file is empty.")
        return

    for line in lines[-25:]:
        print(line)


def main() -> int:
    print("Waiting for backend and frontend...")

    backend_ready = False
    frontend_ready = False

    for second in range(
        1,
        TIMEOUT_SECONDS + 1,
    ):
        if not backend_ready:
            backend_ready = url_ready(
                BACKEND_URL
            )

        if not frontend_ready:
            frontend_ready = url_ready(
                FRONTEND_URL
            )

        backend_text = (
            "READY"
            if backend_ready
            else "starting"
        )

        frontend_text = (
            "READY"
            if frontend_ready
            else "starting"
        )

        print(
            (
                f"\rBackend: {backend_text:<8}  "
                f"Frontend: {frontend_text:<8}  "
                f"{second:>2}s"
            ),
            end="",
            flush=True,
        )

        if (
            backend_ready
            and
            frontend_ready
        ):
            break

        time.sleep(1)

    print()
    print()

    if not backend_ready:
        print(
            "ERROR: Backend did not become ready."
        )

        show_log(
            "backend.log",
            "Backend log",
        )

    if not frontend_ready:
        print(
            "ERROR: Frontend did not become ready."
        )

        show_log(
            "frontend.log",
            "Frontend log",
        )

    if (
        not backend_ready
        or
        not frontend_ready
    ):
        print()
        print(
            "Logs are saved in:"
        )
        print(
            LOG_DIR
        )

        return 1

    print(
        "[OK] Backend ready:  "
        "http://127.0.0.1:8000"
    )

    print(
        "[OK] Frontend ready: "
        "http://127.0.0.1:5173"
    )

    print()
    print(
        "Opening Website QA Agent..."
    )

    webbrowser.open(
        FRONTEND_URL
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
