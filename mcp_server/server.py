#!/usr/bin/env python3
"""Minimal MCP stub for canon tools. Requires optional dep: pip install mcp"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow importing the installed package / src tree
_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

TOOL_SIGNATURES = {
    "list_characters": {"args": {}, "returns": "string[]"},
    "get_canon": {"args": {"character_id": "str"}, "returns": "canon JSON"},
    "build_prompt": {
        "args": {
            "character_id": "str",
            "scene": "str",
            "framing": "str = MCU",
            "wardrobe": "str | None",
            "style_family": "str | None",
        },
        "returns": "{prompt, params, checklist, mj_string}",
    },
}


def _print_todo_and_exit() -> None:
    print("MCP SDK not installed or FastMCP unavailable.", file=sys.stderr)
    print("Install with: pip install -e '.[mcp]'", file=sys.stderr)
    print("Planned tool signatures:", file=sys.stderr)
    print(json.dumps(TOOL_SIGNATURES, indent=2), file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        _print_todo_and_exit()
        return

    from aigc_mv.canon import build_prompt, get_canon, list_character_ids

    mcp = FastMCP("aigc-mv-canon")

    @mcp.tool()
    def list_characters() -> list[str]:
        """List character IDs in the knowledge library."""
        return list_character_ids()

    @mcp.tool()
    def get_canon_tool(character_id: str) -> dict:
        """Return locked identity / wardrobe / style for a character."""
        return get_canon(character_id)

    @mcp.tool()
    def build_prompt_tool(
        character_id: str,
        scene: str,
        framing: str = "MCU",
        wardrobe: str | None = None,
        style_family: str | None = None,
    ) -> dict:
        """Assemble Midjourney-style prompt with verbatim identity."""
        return build_prompt(
            character_id,
            scene=scene,
            framing=framing,
            wardrobe=wardrobe,
            style_family=style_family,
        )

    # FastMCP stdio entry
    mcp.run()


if __name__ == "__main__":
    main()
