# Pipeline overview

## Layers

1. **Knowledge (canon)** — YAML characters + guides. Tools: `get_canon`, `build_prompt`, `list_characters`.
2. **Pipeline** — `align` → `storyboard` → `preview` (later: plates / I2V / lip-sync / QC).

## Prompt order (`build_prompt`)

framing → **identity (verbatim)** → wardrobe → scene → style family → `no text, no letters, no logos`

## Human gates (recommended)

1. Approve brief + cast  
2. Approve final audio take  
3. Approve storyboard before any paid image/video calls  
4. Approve plate selection  
5. Approve v1 cut  

## Next upgrades

- WhisperX forced alignment instead of equal-split stub  
- Real image APIs (Flux / Midjourney) using `plate_prompt`  
- I2V (Seedance / Kling / …) + optional lip-sync  
- HTTP MCP exposing the same canon tools as Claudia-style gallery
