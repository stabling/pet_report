from __future__ import annotations

import uuid


def new_trace_id(prefix: str = "prt") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:20]}"
