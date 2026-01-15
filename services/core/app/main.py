from fastapi import FastAPI
import os
import time
import json

app = FastAPI(title="nextcrm-core", version="0.0.1")

SERVICE = os.getenv("SERVICE_NAME", "core")
ENV = os.getenv("ENV", "dev")
LOG_MODE = os.getenv("LOG_MODE", "normal")


def log(event: str, **fields):
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "INFO",
        "service": SERVICE,
        "env": ENV,
        "event": event,
        "trace_id": fields.pop("trace_id", None),
        **fields,
    }
    print(json.dumps(payload, ensure_ascii=False), flush=True)


@app.get("/health")
def health():
    log("health_check")
    return {"status": "ok", "service": SERVICE, "env": ENV, "log_mode": LOG_MODE}
# END_FILE


@app.get("/version")
def version():
    return {
        "service": "core",
        "version": "0.1.0-dev",
        "build": "local",
    }
