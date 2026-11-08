# 新片如何套用本 Playbook

1. `mkdir -p projects/<id>/{cast,venue,audio,config,keys,edit/keyframe_qc,docs}`  
2. 复制 `playbook/SHOT_LIST_TEMPLATE.md` → `projects/<id>/docs/shot_list.md` 并填写。  
3. 定妆进 `cast/`；场地进 `venue/`（按 [VENUE_BIBLE.md](VENUE_BIBLE.md)）。  
4. 静帧硬检通过后，才写 `jobs` manifest（`h3_mode=fl2va`）。  
5. 可选：用 `rea-video` 对参考片拉片，差距写入 `docs/GAP_vs_ref.md`。  
6. **烧 GPU 前**向 wen hao 要明确同意。

已挂载项目见：

- [projects/yirenzhixia](../projects/yirenzhixia/README.md)  
- [projects/world_celebrity_battle](../projects/world_celebrity_battle/README.md)
