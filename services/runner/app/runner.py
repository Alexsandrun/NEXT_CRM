import os
import time
import json
import redis

SERVICE = os.getenv("SERVICE_NAME", "runner")
ENV = os.getenv("ENV", "dev")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


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


def main():
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    log("runner_start", redis_url=REDIS_URL)

    while True:
        try:
            r.ping()
            log("runner_tick")
        except Exception as e:
            log("runner_error", error=str(e))
        time.sleep(10)


if __name__ == "__main__":
    main()
# END_FILE
