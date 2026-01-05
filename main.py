# main.py
from __future__ import annotations
import os
import sys

import winapi
from scenario import parse_cli, load_scenario
from agent import run_agent

def main() -> None:
    if os.name != "nt":
        sys.exit("Windows required")

    winapi.init_dpi()

    cli = parse_cli(sys.argv)
    system_prompt, task_prompt, tools_schema = load_scenario(cli["scenario_file"], cli["scenario_num"])

    cfg = {
        "endpoint": "http://localhost:1234/v1/chat/completions",
        "model_id": "qwen/qwen3-vl-2b-instruct",
        "timeout": 240,
        "temperature": 0.2,
        "max_tokens": 2048,
        "target_w": 1344,
        "target_h": 756,
        "dump_screenshots": True,
        "dump_dir": "dumps",
        "dump_prefix": "screen_",
        "dump_start": 1,
        "keep_last_screenshots": 1,
        "max_steps": 50,
        "step_delay": 0.4,
    }

    run_agent(system_prompt, task_prompt, tools_schema, cfg)

if __name__ == "__main__":
    main()
