# defaults.py
from __future__ import annotations

LM_STUDIO_ENDPOINT = "http://localhost:1234/v1/chat/completions"
MODEL_ID = "qwen/qwen3-vl-2b-instruct"
TIMEOUT = 240
MAX_STEPS = 20
STEP_DELAY = 0.4
TEMPERATURE = 0.2
MAX_TOKENS = 2048
TARGET_W = 1344
TARGET_H = 756
DUMP_SCREENSHOTS = True
DUMP_DIR = "dumps"
DUMP_PREFIX = "dump_screen_"
DUMP_START = 1
KEEP_LAST_SCREENSHOTS = 1

SYSTEM_PROMPT = "You control a Windows 11 computer using tool calls only. Tools: take_screenshot, move_mouse(x,y in 0..1000), click_mouse, type_text(text), scroll_down. Coordinates are normalized integers 0..1000: (0,0) top-left, (1000,1000) bottom-right. Workflow: observe (take_screenshot), do ONE action, observe again."

TASK_PROMPT = "Take a screenshot, move mouse to center, click, type hello, take another screenshot."

TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "take_screenshot", "description": "Capture screen.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "move_mouse", "description": "Move mouse (0..1000).", "parameters": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}, "required": ["x", "y"]}}},
    {"type": "function", "function": {"name": "click_mouse", "description": "Left click.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "type_text", "description": "Type text.", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "scroll_down", "description": "Scroll down.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]
