# scenario.py
from __future__ import annotations
import json
import sys
from typing import Any, List, Tuple

def load_scenario(filename: str, scenario_num: int) -> Tuple[str, str, List[Dict[str, Any]]]:
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    shared_system_prompt = ""
    if "=== SHARED_SYSTEM_PROMPT ===" in content:
        parts = content.split("=== SHARED_SYSTEM_PROMPT ===", 1)
        shared_block = parts[1].split("=== SCENARIO", 1)[0]
        shared_system_prompt = shared_block.strip()

    scenarios = content.split("=== SCENARIO ")
    scenario_text = scenarios[scenario_num].strip()

    lines = scenario_text.split("\n")
    system_prompt = shared_system_prompt
    task_prompt = ""
    tools_schema = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("TASK_PROMPT:"):
            task_prompt = stripped[len("TASK_PROMPT:"):].strip()
        elif stripped.startswith("TOOLS_SCHEMA:"):
            tools_schema = json.loads(stripped[len("TOOLS_SCHEMA:"):].strip())

    if not task_prompt or not tools_schema:
        sys.exit("Invalid scenario")

    return system_prompt, task_prompt, tools_schema

def parse_cli(argv: list[str]) -> dict[str, Any]:
    if len(argv) < 3:
        sys.exit("Usage: python main.py <scenario_file> <scenario_num>")
    return {"scenario_file": argv[1], "scenario_num": int(argv[2])}
