# agent.py
from __future__ import annotations
import os
import time
import base64
from typing import Any, Dict, List, Tuple

import winapi
from llm_client import post_to_lm
from agent_utils import parse_coords, parse_text, prune_old_screenshots, get_disabled_tools

def run_agent(system_prompt: str, task_prompt: str, tools_schema: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    endpoint = cfg["endpoint"]
    model_id = cfg["model_id"]
    timeout = cfg["timeout"]
    temperature = cfg["temperature"]
    max_tokens = cfg["max_tokens"]
    target_w = cfg["target_w"]
    target_h = cfg["target_h"]
    dump_screenshots = cfg["dump_screenshots"]
    dump_dir = cfg["dump_dir"]
    dump_prefix = cfg["dump_prefix"]
    dump_start = cfg["dump_start"]
    keep_last_screenshots = cfg["keep_last_screenshots"]
    max_steps = cfg["max_steps"]
    step_delay = cfg["step_delay"]

    disabled = get_disabled_tools(tools_schema)
    os.makedirs(dump_dir, exist_ok=True)

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_prompt},
    ]

    dump_idx = dump_start
    last_screen_w, last_screen_h = winapi.get_screen_size()

    for _step in range(max_steps):
        resp = post_to_lm({
            "model": model_id,
            "messages": messages,
            "tools": tools_schema,
            "tool_choice": "auto",
            "temperature": temperature,
            "max_tokens": max_tokens,
        }, endpoint, timeout)

        msg = resp["choices"][0]["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            break

        for tc in tool_calls:
            name = tc["function"]["name"]
            arg_str = tc["function"].get("arguments", "{}")
            call_id = tc["id"]

            if name in disabled:
                messages.append({"role": "tool", "tool_call_id": call_id, "name": name, "content": "error tool_disabled"})
                continue

            if name == "take_screenshot":
                png_bytes, screen_w, screen_h = winapi.capture_screenshot_png(target_w, target_h)
                last_screen_w, last_screen_h = screen_w, screen_h

                fn = None
                if dump_screenshots:
                    fn = os.path.join(dump_dir, f"{dump_prefix}{dump_idx:04d}.png")
                    with open(fn, "wb") as f:
                        f.write(png_bytes)
                    dump_idx += 1

                winapi.cursor_pos_normalized(screen_w, screen_h)
                tool_text = "ok" if fn is None else ("ok file=" + fn)
                b64 = base64.b64encode(png_bytes).decode("ascii")

                messages.append({"role": "tool", "tool_call_id": call_id, "name": name, "content": tool_text})
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "screen"},
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
                    ],
                })
                messages = prune_old_screenshots(messages, keep_last_screenshots)

            elif name == "move_mouse":
                xn, yn = parse_coords(arg_str)
                screen_w, screen_h = winapi.move_mouse_norm(xn, yn)
                time.sleep(0.06)
                cx, cy, cnx, cny = winapi.cursor_pos_normalized(screen_w, screen_h)
                messages.append({"role": "tool", "tool_call_id": call_id, "name": name, "content": f"ok cursor_px={cx},{cy} cursor_norm={cnx},{cny}"})

            elif name == "click_mouse":
                winapi.click_mouse()
                time.sleep(0.06)
                cx, cy, cnx, cny = winapi.cursor_pos_normalized(last_screen_w, last_screen_h)
                messages.append({"role": "tool", "tool_call_id": call_id, "name": name, "content": f"ok cursor_px={cx},{cy} cursor_norm={cnx},{cny}"})

            elif name == "type_text":
                text = parse_text(arg_str)
                winapi.type_text(text)
                time.sleep(0.06)
                cx, cy, cnx, cny = winapi.cursor_pos_normalized(last_screen_w, last_screen_h)
                messages.append({"role": "tool", "tool_call_id": call_id, "name": name, "content": f"ok typed={text} cursor_px={cx},{cy} cursor_norm={cnx},{cny}"})

            elif name == "scroll_down":
                winapi.scroll_down()
                time.sleep(0.06)
                cx, cy, cnx, cny = winapi.cursor_pos_normalized(last_screen_w, last_screen_h)
                messages.append({"role": "tool", "tool_call_id": call_id, "name": name, "content": f"ok cursor_px={cx},{cy} cursor_norm={cnx},{cny}"})

            else:
                messages.append({"role": "tool", "tool_call_id": call_id, "name": name, "content": "error unknown_tool"})

        time.sleep(step_delay)
