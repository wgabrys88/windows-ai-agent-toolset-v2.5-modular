# agent_utils.py
from __future__ import annotations
import json
from typing import Any, List, Dict, Tuple

def parse_coords(arg_str: Any) -> Tuple[float, float]:
    try:
        a = json.loads(arg_str) if isinstance(arg_str, str) else (arg_str or {})
    except:
        a = {}
    if isinstance(a, dict):
        x, y = a.get("x", 500), a.get("y", 500)
    elif isinstance(a, (list, tuple)) and len(a) >= 2:
        x, y = a[0], a[1]
    else:
        x, y = 500, 500
    try:
        x = float(x)
    except:
        x = 500.0
    try:
        y = float(y)
    except:
        y = 500.0
    x = max(0.0, min(1000.0, x))
    y = max(0.0, min(1000.0, y))
    return x, y

def parse_text(arg_str: Any) -> str:
    try:
        a = json.loads(arg_str) if isinstance(arg_str, str) else (arg_str or {})
    except:
        a = {}
    t = a.get("text", "") if isinstance(a, dict) else ""
    return str(t) if t is not None else ""

def prune_old_screenshots(messages: List[Dict[str, Any]], keep_last: int) -> List[Dict[str, Any]]:
    if keep_last <= 0:
        return [m for m in messages if not (m.get("role") == "user" and isinstance(m.get("content"), list))]
    idxs = [i for i, m in enumerate(messages) if m.get("role") == "user" and isinstance(m.get("content"), list)]
    if len(idxs) <= keep_last:
        return messages
    drop = set(idxs[:-keep_last])
    return [m for i, m in enumerate(messages) if i not in drop]
