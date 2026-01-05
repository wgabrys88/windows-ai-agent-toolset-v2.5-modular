# scenario.py
from __future__ import annotations
import json
import sys
from typing import Any, Dict, List, Tuple

def load_scenario(filename: str, scenario_num: int) -> Tuple[str, str, List[Dict[str, Any]]]:
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    shared_system_prompt = None
    if "=== SHARED_SYSTEM_PROMPT ===" in content:
        parts = content.split("=== SHARED_SYSTEM_PROMPT ===", 1)
        shared_block = parts[1].split("=== SCENARIO", 1)[0]
        shared_system_prompt = shared_block.strip()
    scenarios = content.split("=== SCENARIO ")
    scenario_text = scenarios[scenario_num]
    lines = scenario_text.strip().split("\n")
    system_prompt = shared_system_prompt or ""
    task_prompt = None
    tools_schema = None
    for raw in lines:
        line = raw.strip()
        if line.startswith("SYSTEM_PROMPT:"):
            system_prompt = line[len("SYSTEM_PROMPT:"):].strip()
        elif line.startswith("TASK_PROMPT:"):
            task_prompt = line[len("TASK_PROMPT:"):].strip()
        elif line.startswith("TOOLS_SCHEMA:"):
            tools_schema_str = line[len("TOOLS_SCHEMA:"):].strip()
            tools_schema = json.loads(tools_schema_str)
    if not system_prompt or not task_prompt or not tools_schema:
        sys.exit(1)
    return system_prompt, task_prompt, tools_schema

def parse_cli(argv: List[str]) -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    if len(argv) >= 3 and not argv[1].startswith("-"):
        cfg["scenario_file"] = argv[1]
        cfg["scenario_num"] = int(argv[2])
        rest = argv[3:]
    else:
        rest = argv[1:]
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--dump_dir" and i + 1 < len(rest):
            cfg["dump_dir"] = rest[i + 1]
            i += 2
        elif a == "--keep_screens" and i + 1 < len(rest):
            cfg["keep_screens"] = int(rest[i + 1])
            i += 2
        elif a == "--max_steps" and i + 1 < len(rest):
            cfg["max_steps"] = int(rest[i + 1])
            i += 2
        else:
            i += 1
    return cfg
