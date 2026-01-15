from fastapi import FastAPI
import os
import time
import json

app = FastAPI(title="nextcrm-content", version="0.0.1")

SERVICE = os.getenv("SERVICE_NAME", "content")
ENV = os.getenv("ENV", "dev")
DATA_DIR = os.getenv("CONTENT_DATA_DIR", "/data")


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
    log("health_check", data_dir=DATA_DIR)
    return {"status": "ok", "service": SERVICE, "env": ENV, "data_dir": DATA_DIR}
# END_FILE
