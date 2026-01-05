# smart_combine.py
from __future__ import annotations
import os
import sys
import argparse
import importlib.abc
import importlib.util
from typing import Dict, List, Tuple

FILES: List[Tuple[str, str]] = [
    ("defaults", "defaults.py"),
    ("winapi", "winapi.py"),
    ("llm_client", "llm_client.py"),
    ("scenario", "scenario.py"),
    ("agent_utils", "agent_utils.py"),
    ("agent", "agent.py"),
    ("main", "main.py"),
]

def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def build_ai_bundle(root: str) -> str:
    parts: List[str] = []
    for name, fn in FILES:
        path = os.path.join(root, fn)
        src = _read_text(path)
        parts.append("FILE: " + fn + "\n")
        parts.append(src.rstrip() + "\n")
        parts.append("\n" + ("-" * 72) + "\n\n")
    return "".join(parts)

def build_onefile(root: str) -> str:
    embed: Dict[str, str] = {}
    for name, fn in FILES:
        path = os.path.join(root, fn)
        embed[name] = _read_text(path)

    lines: List[str] = []
    lines.append("from __future__ import annotations\n")
    lines.append("import sys\n")
    lines.append("import importlib.abc\n")
    lines.append("import importlib.util\n")
    lines.append("\n")
    lines.append("EMBEDDED = {\n")
    for k in embed:
        lines.append(repr(k) + ": " + repr(embed[k]) + ",\n")
    lines.append("}\n")
    lines.append("\n")
    lines.append("class _EmbeddedLoader(importlib.abc.Loader):\n")
    lines.append("    def __init__(self, name: str, src: str):\n")
    lines.append("        self.name = name\n")
    lines.append("        self.src = src\n")
    lines.append("    def create_module(self, spec):\n")
    lines.append("        return None\n")
    lines.append("    def exec_module(self, module):\n")
    lines.append("        exec(self.src, module.__dict__)\n")
    lines.append("\n")
    lines.append("class _EmbeddedFinder(importlib.abc.MetaPathFinder):\n")
    lines.append("    def find_spec(self, fullname, path=None, target=None):\n")
    lines.append("        if fullname in EMBEDDED:\n")
    lines.append("            loader = _EmbeddedLoader(fullname, EMBEDDED[fullname])\n")
    lines.append("            return importlib.util.spec_from_loader(fullname, loader, origin='embedded')\n")
    lines.append("        return None\n")
    lines.append("\n")
    lines.append("sys.meta_path.insert(0, _EmbeddedFinder())\n")
    lines.append("import main as _main\n")
    lines.append("_main.main()\n")
    return "".join(lines)

def main() -> None:
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("--mode", choices=["ai", "onefile"], default="ai")
    p.add_argument("--out", default=None)
    p.add_argument("--root", default=None)
    args = p.parse_args()

    root = args.root or os.path.dirname(os.path.abspath(__file__))
    if args.mode == "ai":
        out = args.out or os.path.join(root, "ai_bundle.txt")
        _write_text(out, build_ai_bundle(root))
    else:
        out = args.out or os.path.join(root, "combined_onefile.py")
        _write_text(out, build_onefile(root))

if __name__ == "__main__":
    main()
