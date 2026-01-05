# main.py
from __future__ import annotations
import os
import sys
from typing import Any, Dict

import defaults
import winapi
from scenario import parse_cli, load_scenario
from agent import run_agent

def main() -> None:
    if os.name != "nt":
        raise OSError("Windows required")

    winapi.init_dpi()

    cli = parse_cli(sys.argv)

    system_prompt = defaults.SYSTEM_PROMPT
    task_prompt = defaults.TASK_PROMPT
    tools_schema = defaults.TOOLS_SCHEMA

    if "scenario_file" in cli and "scenario_num" in cli:
        system_prompt, task_prompt, tools_schema = load_scenario(cli["scenario_file"], cli["scenario_num"])

    cfg: Dict[str, Any] = {
        "endpoint": defaults.LM_STUDIO_ENDPOINT,
        "model_id": defaults.MODEL_ID,
        "timeout": defaults.TIMEOUT,
        "max_steps": defaults.MAX_STEPS,
        "step_delay": defaults.STEP_DELAY,
        "temperature": defaults.TEMPERATURE,
        "max_tokens": defaults.MAX_TOKENS,
        "target_w": defaults.TARGET_W,
        "target_h": defaults.TARGET_H,
        "dump_screenshots": defaults.DUMP_SCREENSHOTS,
        "dump_dir": defaults.DUMP_DIR,
        "dump_prefix": defaults.DUMP_PREFIX,
        "dump_start": defaults.DUMP_START,
        "keep_last_screenshots": defaults.KEEP_LAST_SCREENSHOTS,
    }

    if "dump_dir" in cli:
        cfg["dump_dir"] = cli["dump_dir"]
    if "keep_screens" in cli:
        cfg["keep_last_screenshots"] = max(0, int(cli["keep_screens"]))
    if "max_steps" in cli:
        cfg["max_steps"] = max(0, int(cli["max_steps"]))

    run_agent(system_prompt, task_prompt, tools_schema, cfg)

if __name__ == "__main__":
    main()
