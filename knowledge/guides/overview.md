# Pipeline overview

## Layers

1. **Knowledge (canon)** — YAML characters + guides. Tools: `get_canon`, `build_prompt`, `list_characters`.
2. **Knowledge (lore · 典故)** — YAML classical anecdote cards for MV plot + lyrics. Tools: `list_lore`, `get_lore`, `lyric-brief`. Creative rule: **借古讽今，但不讽刺政治**（友情、职场信用、手艺/长期主义等）. See [`../lore/README.md`](../lore/README.md).
3. **Pipeline** — `align` → `storyboard` → `preview` (later: plates / I2V / lip-sync / QC). When `brief.yaml` has `lore_id`, storyboard lightly injects allegory/themes into shot action and plate context.

## Prompt order (`build_prompt`)

framing → **identity (verbatim)** → wardrobe → scene → style family → `no text, no letters, no logos`

## Human gates (recommended)

1. Approve brief + cast + lore card  
2. Approve final audio take  
3. Approve storyboard before any paid image/video calls  
4. Approve plate selection  
5. Approve v1 cut  

## Next upgrades

- WhisperX forced alignment instead of equal-split stub  
- Real image APIs (Flux / Midjourney) using `plate_prompt`  
- I2V (Seedance / Kling / …) + optional lip-sync  
- HTTP MCP exposing the same canon/lore tools as Claudia-style gallery
