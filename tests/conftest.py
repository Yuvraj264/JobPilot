import threading
import time
import urllib.request
import pytest
import uvicorn
from app.main import app


def _start_uvicorn_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")


@pytest.fixture(scope="session", autouse=True)
def live_server():
    """
    Session fixture ensuring FastAPI live server runs on http://127.0.0.1:8000
    so Playwright Chromium can navigate mock application pages during tests.
    """
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=0.5) as resp:
            if resp.status == 200:
                yield
                return
    except Exception:
        pass

    server_thread = threading.Thread(target=_start_uvicorn_server, daemon=True)
    server_thread.start()

    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=0.5) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.1)

    yield
