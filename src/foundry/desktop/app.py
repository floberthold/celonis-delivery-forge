import os
import socket
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

import uvicorn


HOST = "127.0.0.1"
PORT = 8000
DASHBOARD_URL = f"http://{HOST}:{PORT}/"
HEALTH_URL = f"http://{HOST}:{PORT}/health"
HEALTH_TIMEOUT_SECONDS = 40


def _app_dir() -> Path:
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        local_app_data = str(Path.home() / "AppData" / "Local")
    path = Path(local_app_data) / "CelonisDeliveryForge"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _db_url() -> str:
    db_path = _app_dir() / "foundry.db"
    return f"sqlite:///{db_path.as_posix()}"


def _log_file() -> Path:
    return _app_dir() / "desktop.log"


def _log(message: str) -> None:
    line = f"{datetime.now().isoformat(timespec='seconds')} {message}"
    try:
        with _log_file().open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        pass


def _is_port_occupied(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _wait_for_health(url: str, timeout_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    return False


def run_server() -> None:
    try:
        _log("Starting uvicorn server")
        uvicorn.run("foundry.api.main:app", host=HOST, port=PORT, reload=False)
    except Exception:
        _log("Server thread crashed:\n" + traceback.format_exc())
        raise


def run_desktop() -> None:
    try:
        if not os.getenv("FORGE_DATABASE_URL"):
            os.environ["FORGE_DATABASE_URL"] = _db_url()
            _log("FORGE_DATABASE_URL not set; defaulted to LocalAppData SQLite")

        if _is_port_occupied(HOST, PORT):
            _log(f"Port {PORT} already occupied; opening dashboard and exiting")
            webbrowser.open(DASHBOARD_URL)
            return

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()

        if _wait_for_health(HEALTH_URL, HEALTH_TIMEOUT_SECONDS):
            _log("Health check ready; opening dashboard")
            webbrowser.open(DASHBOARD_URL)
        else:
            _log(f"Health check failed after {HEALTH_TIMEOUT_SECONDS}s; not opening browser")

        while thread.is_alive():
            thread.join(timeout=1.0)
    except Exception:
        _log("Desktop launcher failed:\n" + traceback.format_exc())
        raise


if __name__ == "__main__":
    run_desktop()
