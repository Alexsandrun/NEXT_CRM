from __future__ import annotations

import uuid
from typing import Any

from starlette.responses import JSONResponse


def new_trace_id() -> str:
    # Dev-simple trace id (we can switch to ULID later)
    return uuid.uuid4().hex


def error_body(
    *,
    code: str,
    message: str,
    trace_id: str | None = None,
    details: dict[str, Any] | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    tid = trace_id or new_trace_id()
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "retryable": bool(retryable),
        },
        "trace_id": tid,
    }
    if details:
        body["error"]["details"] = details
    return body


def http_error(
    *,
    status_code: int,
    code: str,
    message: str,
    trace_id: str | None = None,
    details: dict[str, Any] | None = None,
    retryable: bool = False,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_body(
            code=code,
            message=message,
            trace_id=trace_id,
            details=details,
            retryable=retryable,
        ),
    )


# END_FILE
