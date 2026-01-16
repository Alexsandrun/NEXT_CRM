import os
import time

import requests

BASE = os.environ.get("BASE", "http://localhost:8088")


def wait_for_health(timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        try:
            r = requests.get(f"{BASE}/api/health", timeout=2)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError("Service did not become healthy in time")


def test_health_and_version():
    j = wait_for_health(timeout=20)
    assert j.get("status") == "ok"

    r = requests.get(f"{BASE}/api/version", timeout=3)
    assert r.status_code == 200
    v = r.json()
    assert "service" in v


def test_bootstrap_login_whoami_and_logout():
    # bootstrap may be idempotent; ensure it returns success
    r = requests.post(f"{BASE}/api/bootstrap", timeout=5)
    assert r.status_code in (200, 201)

    login_payload = {
        "tenant": "demo",
        "email": "admin@demo.local",
        "password": "admin123",
    }
    r2 = requests.post(f"{BASE}/api/auth/login", json=login_payload, timeout=5)
    assert r2.status_code == 200, r2.text
    tok = r2.json().get("access_token")
    assert tok, r2.text

    # whoami
    r3 = requests.get(
        f"{BASE}/api/auth/whoami", headers={"Authorization": f"Bearer {tok}"}, timeout=3
    )
    assert r3.status_code == 200, r3.text
    j = r3.json()
    assert j.get("user_id") is not None

    # logout
    r4 = requests.post(
        f"{BASE}/api/auth/logout", headers={"Authorization": f"Bearer {tok}"}, timeout=3
    )
    assert r4.status_code == 200 or r4.status_code == 204

    # whoami after logout should be unauthorized (401) or 403
    r5 = requests.get(
        f"{BASE}/api/auth/whoami", headers={"Authorization": f"Bearer {tok}"}, timeout=3
    )
    assert r5.status_code in (401, 403)
