# 新片如何套用本 Playbook

1. `mkdir -p projects/<id>/{cast,venue,audio,config,keys,edit/keyframe_qc,docs}`  
2. 复制 `playbook/SHOT_LIST_TEMPLATE.md` → `projects/<id>/docs/shot_list.md` 并填写。  
3. 定妆进 `cast/`；场地进 `venue/`（按 [VENUE_BIBLE.md](VENUE_BIBLE.md)）。  
4. 静帧与控制流硬检通过后，由 `aigc-mv ep prompts` 生成带 H3 双轨路由（`ref2va_pose` / `ref2va_depth` / `fl2va_morph`）的单元配置。  
5. 粗剪与成片必跑 `aigc-mv ep rea-audit --check-flow --strict` 对标《火影有嘻哈》基准，差距写入 `edit/rea_audit.md`。  
6. **烧 GPU 前**先过 `aigc-mv ep approve` 预算门禁并确认审批。

已挂载项目见：

- [projects/yirenzhixia](../projects/yirenzhixia/README.md)  
- [projects/world_celebrity_battle](../projects/world_celebrity_battle/README.md)
