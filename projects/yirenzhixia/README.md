# 一人之下 · 项目挂载

套用仓库根目录 [`playbook/`](../../playbook/)。

## 范围

- MV / 擂台类短片，例如《雷有两面》、综艺向《罗天大醮有嘻哈》等。
- 仓库里已有一期示例工程：[`../wangye_vs_zhugeqing`](../wangye_vs_zhugeqing/)（诸葛青 VS 王也，`format: show`）。**本目录是 IP 级索引 + 焚诀门禁说明**；具体一期仍用 `projects/<一期>/` 的 episode 结构。

## 与 playbook 的接法

| Playbook 步骤 | 本仓 CLI / 目录 |
|---|---|
| 先剪后拆 | `aigc-mv ep board` → `board/board.md` 确认后再花钱 |
| 定妆多角度 | `ep refs` 三步定妆 + `ep sheets` 组图；三一门 / 全性新增知识卡见 `knowledge/characters/`（`lu_jin`、`li_muxuan`、`lu_linglong`、`zuo_ruotong`）与 `knowledge/lore/`（`nisheng_sanchong`、`tongtianlu`） |
| 首尾帧与群像硬检 | 见 `playbook/KEYFRAME_QC.md`；观众席优先用已有剧照 `img2img`，器乐必须由角色本人上台演奏 |
| H3 双轨制路由 | `ep prompts` 自动写入 `h3_routing`：主唱默认 `ref2va_pose`（21 点去脸骨骼 `0.72@0.84`），武打/器乐/群像默认 `ref2va_depth`（`0.68@0.82`），仅跨年龄/状态变身用 `fl2va_morph` |
| Venue Bible | `refs/venue.png` + 文字规则；复杂场地另建 `venue/` |
| `rea-video` 闭环门禁 | `aigc-mv ep rea-audit --video final/<片名>.mp4 --rea-dir edit/rea_out --check-flow` 对标《火影有嘻哈》硬指标 |

## 外部大工程（未整包入库）

- 本机 `/workspace/films/luotian_ep02_v10_plan/` — 《雷有两面》ep02 焚诀案、Venue Bible、rea-video 差距  
- 《异人开麦 ep03：三重修在心里面》v6 成片与工程包 — 见 [`../world_celebrity_battle/README.md`](../world_celebrity_battle/README.md) 及 [实战演进报告](../../docs/火影有嘻哈_rea_video拉片与ep03实战演进.md)
- Drive 成片 / 场地圣经链接写在各期 README，不进 Git

## 开下一集检查单

- [ ] 挂点 / 分镜表确认（board 审核 PASS）  
- [ ] 主创定妆 sheet 齐套  
- [ ] 场地轴线与灯光 cue 锁定  
- [ ] 首帧 / 变换尾帧与群像 `img2img` 硬检  
- [ ] 预算门禁批准后再提交生成 / 烧 GPU  
- [ ] 成片跑 `ep rea-audit` 确认 `still_motion <= 3%`、`moving >= 90%`、`jump <= 1`

