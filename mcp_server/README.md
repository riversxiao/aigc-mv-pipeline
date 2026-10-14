# MCP server (optional)

Expose the same knowledge tools Claudia-style gallery uses, against **your** characters.

## Planned tools

| Tool | Args | Returns |
|------|------|---------|
| `list_characters` | — | `string[]` ids |
| `get_canon` | `character_id: str` | canon JSON |
| `build_prompt` | `character_id`, `scene`, `framing?`, `wardrobe?`, `style_family?` | `{prompt, params, checklist, mj_string}` |

## Run (when deps installed)

```bash
pip install -e ".[mcp]"
python mcp_server/server.py
# then: claude mcp add --transport stdio aigc-mv -- python /path/to/mcp_server/server.py
# or switch to Streamable HTTP and:
# claude mcp add --transport http aigc-mv http://127.0.0.1:8765/mcp
```

`server.py` tries FastMCP if `mcp` is installed; otherwise it prints tool signatures and exits with a clear message.
