import json
from typing import Any, Dict, Optional


def make_result(
    ok: bool, code: str, reason: str = "", data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return {
        "ok": bool(ok),
        "code": code,
        "reason": reason,
        "data": data or {},
    }


def emit_result(result: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
