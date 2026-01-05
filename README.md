# Windows 11 AI Automation Agent (Modular)

This repository contains a Windows 11 automation agent designed for AI tool use (screenshot + mouse + keyboard), implemented with Python standard library only and Win32 APIs via `ctypes`.

## Repository layout

- `main.py`
  - Entry point and top-level orchestration.
  - Loads defaults, applies CLI overrides, initializes DPI, loads scenario (optional), and runs the agent loop.
- `defaults.py`
  - All default constants (LM endpoint/model, loop settings, screenshot settings).
  - Default `SYSTEM_PROMPT`, `TASK_PROMPT`, and `TOOLS_SCHEMA`.
- `winapi.py`
  - All Windows/ctypes/Win32 functionality.
  - DPI awareness, screen metrics, cursor, screenshot capture (GDI + cursor overlay), PNG encoding, mouse and keyboard input.
  - Exposes a stable platform API used by the agent.
- `llm_client.py`
  - LM Studio client function `post_to_lm(...)` (OpenAI-compatible `/v1/chat/completions`).
- `scenario.py`
  - Scenario file loading and CLI parsing.
  - Allows overriding prompts and tool schema from a scenario file.
- `agent_utils.py`
  - Tool argument parsing (`parse_coords`, `parse_text`), screenshot message pruning, and disabled tool detection.
- `agent.py`
  - The agent runtime loop.
  - Calls the LLM, executes tool calls, appends tool results and screenshot messages, and manages conversation state.
- `smart_combine.py`
  - Last-resort bundling script:
    - `--mode ai` produces a single text bundle of all files for AI context.
    - `--mode onefile` produces a runnable single-file version embedding all modules.

## Module boundaries and the stable platform API

The design intentionally isolates the Windows implementation details inside `winapi.py`. The rest of the system treats `winapi` as a stable platform layer.

The primary functions the agent relies on:

- `winapi.init_dpi()` (alias `setup_dpi()` also exists)
- `winapi.get_screen_size() -> (screen_w, screen_h)`
- `winapi.capture_screenshot_png(target_w, target_h) -> (png_bytes, screen_w, screen_h)`
- `winapi.cursor_pos_normalized(screen_w, screen_h) -> (cx, cy, xn, yn)`
- `winapi.move_mouse_norm(xn, yn) -> (screen_w, screen_h)`
- `winapi.click_mouse()`
- `winapi.scroll_down()`
- `winapi.type_text(text)`

If you add new automation features, keep the "agent <-> winapi" interface narrow and consistent. Most future work should happen inside `winapi.py` or `agent.py` without requiring full-repo changes.

## How the system works (data flow)

### 1) Startup and configuration flow

1. `main.py` starts.
2. `winapi.init_dpi()` enables per-monitor DPI awareness.
3. `scenario.parse_cli(sys.argv)` reads CLI:
   - optional scenario selection (scenario file + index)
   - optional overrides (dump dir, keep screens, max steps)
4. Defaults are loaded from `defaults.py`.
5. If scenario is provided:
   - `scenario.load_scenario(...)` returns `(system_prompt, task_prompt, tools_schema)`.
6. A `cfg` dictionary is assembled (endpoint, model, timeouts, target capture size, dumping settings, etc.).
7. `agent.run_agent(system_prompt, task_prompt, tools_schema, cfg)` starts the agent loop.

### 2) LLM request/response flow

Inside `agent.run_agent(...)`:

1. The conversation `messages` list is initialized:
   - `{"role": "system", "content": system_prompt}`
   - `{"role": "user", "content": task_prompt}`
2. For each step (up to `max_steps`):
   - `llm_client.post_to_lm(payload, endpoint, timeout)` is called with:
     - `model`
     - `messages`
     - `tools` = `tools_schema`
     - `tool_choice` = `"auto"`
     - `temperature`, `max_tokens`
3. The assistant message from the LLM is appended to `messages`.
4. If the assistant message includes `tool_calls`, the agent executes them sequentially.

### 3) Tool execution flow

Each tool call is handled by name:

- `take_screenshot`
  1. `winapi.capture_screenshot_png(target_w, target_h)` returns:
     - `png_bytes` (PNG of target resolution)
     - `screen_w, screen_h` (physical screen size in pixels)
  2. Optional dump: write PNG to `dump_dir`.
  3. The tool result is appended as a `"tool"` message.
  4. A *new user message* containing the image is appended:
     - `{"type":"image_url","image_url":{"url":"data:image/png;base64,..."} }`
  5. `agent_utils.prune_old_screenshots(messages, keep_last)` removes older screenshot messages so context does not grow unbounded.

- `move_mouse`
  1. Parse args via `agent_utils.parse_coords(arguments)`.
  2. `winapi.move_mouse_norm(xn, yn)`.
  3. Cursor state is read via `winapi.cursor_pos_normalized(...)`.
  4. Tool result appended.

- `click_mouse`, `type_text`, `scroll_down`
  1. Call the matching `winapi` function.
  2. Cursor state reported via `cursor_pos_normalized(...)`.
  3. Tool result appended.

This continues until the LLM returns no tool calls or `max_steps` is reached.

## How tools connect to code

- The LLM is given `TOOLS_SCHEMA` (from `defaults.py` or scenario).
- The agent dispatch uses the tool names as keys:
  - Tool schema name must match the `if name == "..."` branches in `agent.py`.
- If you add a new tool:
  1. Add it to `TOOLS_SCHEMA`.
  2. Add a handler branch in `agent.py`.
  3. Implement the feature in `winapi.py` (preferred) or in agent-level logic if it is not Win32-specific.

## Development workflow suggestions

### Typical edits by module

- Input/screenshot bugs, DPI issues, performance in capture:
  - Edit `winapi.py`
- Tool definition changes, new tool, revised agent loop logic:
  - Edit `agent.py` and `defaults.py` (or scenario file)
- Scenario file format changes or CLI flags:
  - Edit `scenario.py`
- Prompt shaping, model config, defaults:
  - Edit `defaults.py`
- LLM request changes, headers/timeouts:
  - Edit `llm_client.py`
- Argument parsing and message pruning:
  - Edit `agent_utils.py`

### When you need a single-file artifact

Use `smart_combine.py` as a last resort:

- Create a single AI-readable bundle (best for AI context):
  - `python smart_combine.py --mode ai`
  - Output defaults to `ai_bundle.txt`

- Create a runnable single-file combined script:
  - `python smart_combine.py --mode onefile`
  - Output defaults to `combined_onefile.py`

## How to prompt AI effectively with this repository

Different assistants/environments have different abilities:
- Some can browse GitHub links and read multiple files.
- Some cannot browse or will miss files unless you paste them.

The goal is to ensure the assistant always sees enough context to make correct changes.

### Recommended approach (most reliable)

1. Generate `ai_bundle.txt`:
   - `python smart_combine.py --mode ai`
2. Paste `ai_bundle.txt` contents into the chat.

This guarantees the assistant sees the entire codebase in the intended order.

### If you want to give the GitHub link

When the assistant can browse:
- Provide the repository link and explicitly instruct it to read all files listed below before proposing changes.

Use a prompt like:

- "Read all repository files: defaults.py, winapi.py, llm_client.py, scenario.py, agent_utils.py, agent.py, main.py, smart_combine.py. Summarize the module responsibilities and call graph. Then implement X. Only modify the minimum necessary files."

If the assistant cannot browse:
- Paste `ai_bundle.txt` instead.

### Prompts you will likely ask in the future

Below are practical prompt templates that work well with this modular architecture.

#### A) Whole-system change (new tool / new capability)

- "Using this repo, add a new tool named `scroll_up` with the same style as `scroll_down`. Update TOOLS_SCHEMA, agent dispatch, and implement in winapi.py. Keep behavior silent and Windows-only. Return only modified files."

- "Add a tool `right_click`. Update schema and dispatch. Implement in winapi.py using SendInput. Return only modified files."

- "Add multi-monitor screenshot support while keeping the normalized 0..1000 coordinates consistent. Propose the minimum API changes required in winapi.py and agent.py."

#### B) Win32-only work (most common)

- "Focus only on winapi.py: improve screenshot performance without external deps. Keep output identical (PNG, cursor overlay). Return only winapi.py."

- "In winapi.py, add a function `scroll(amount)` where amount is integer multiples of 120. Update agent to accept an argument for scrolling. Return modified files."

- "Investigate coordinate mapping correctness in winapi.py for DPI scaling and suggest fixes with minimal changes."

#### C) Agent loop and prompting work

- "Focus on agent.py and defaults.py: adjust the observation/action loop to enforce exactly one tool call per step. If multiple tool_calls are returned, execute only the first and request another model step. Return modified files."

- "Update screenshot pruning strategy in agent_utils.py so only the last N images remain, but keep the last tool results always. Return only agent_utils.py and agent.py if needed."

#### D) Scenario and CLI work

- "Extend scenario.py to support additional CLI flags: --target_w, --target_h, --temperature. Wire them into main.py config. Return modified files."

- "Change scenario file parsing to support multi-line prompts for SYSTEM_PROMPT and TASK_PROMPT blocks. Return only scenario.py and any other necessary file."

#### E) Debugging and root-cause analysis prompts

- "Read all files and produce a call graph and data flow. Then explain likely causes if screenshots are black or cursor overlay is missing. Suggest fixes in winapi.py."

- "Tool calls return ok but mouse does not move on some machines. Review winapi.py SetCursorPos/SendInput usage and propose robust fallbacks."

### A minimal instruction block to include in any future AI request

Copy/paste this when starting a new AI conversation:

- "Before changing anything: read all files in the repo (or the provided ai_bundle). Identify which module owns the change: winapi.py for Windows/ctypes features; agent.py for tool dispatch and conversation loop; defaults.py for schema and configuration; scenario.py for scenario/CLI; llm_client.py for network calls; agent_utils.py for parsing and pruning; main.py for wiring. Then propose a minimal diff and return only the files that must change."

## Connection map (how things depend on each other)

- `main.py`
  - imports `defaults`, `winapi`, `scenario`, `agent`
- `agent.py`
  - imports `winapi`, `llm_client.post_to_lm`, `agent_utils.*`
- `scenario.py`
  - standalone parsing/loading
- `agent_utils.py`
  - standalone parsing/pruning
- `llm_client.py`
  - standalone HTTP client
- `winapi.py`
  - standalone Win32/ctypes platform layer

No module depends on `main.py`. The most common working set for changes is:
- `winapi.py` alone, or
- `agent.py` + `defaults.py`, sometimes with `agent_utils.py`.

## Notes for maintaining AI friendliness

- Keep tool names stable and centralized (schema in `defaults.py` or scenario files).
- Keep Win32 details isolated in `winapi.py`.
- When asking AI to change something, name the target module(s) explicitly.
- When in doubt, provide `ai_bundle.txt` generated by `smart_combine.py --mode ai`.
