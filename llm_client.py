# llm_client.py
from __future__ import annotations
import json
import urllib.request
from typing import Any, Dict

def post_to_lm(payload: Dict[str, Any], endpoint: str, timeout: int) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))
