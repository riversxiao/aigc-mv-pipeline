# Playbook · 跨项目制片纪律

本目录把「焚诀」对齐后的 **可复用流程** 从单集工程里抽出来，给：

- **一人之下**（`projects/yirenzhixia/`，含《雷有两面》等 MV）
- **世界名人大乱斗 / 异人开麦**（`projects/world_celebrity_battle/`）
- 酒楼诗人及其他新片

共用同一套门禁；**角色、场地、曲目只挂在各自 `projects/<id>/`**。

上游灵感：[MinLiBuilds「焚诀」/ copy-kakasi](https://github.com/limin112/min-skill/tree/main/skills/copy-kakasi)（我们只借七步纪律与 fl2va 优先，不照搬换脸复刻真人流程）。

## 一句话

质感差通常不是少写几个 cinematic 词，而是中间三步缺失：

1. 先剪辑确认再生成  
2. 定妆多角度  
3. **每镜首尾帧硬检** 后再 H3 **fl2va**（人物主镜禁用 ref2va）

## 文档索引

| 文件 | 用途 |
|---|---|
| [PIPELINE.md](PIPELINE.md) | 七步流水线 + P0/P1 优先级 |
| [SHOT_LIST_TEMPLATE.md](SHOT_LIST_TEMPLATE.md) | 挂点 / 分镜表模板 |
| [KEYFRAME_QC.md](KEYFRAME_QC.md) | 首尾帧 5 项硬检 |
| [DIRECTORY.md](DIRECTORY.md) | 工程目录约定 |
| [VENUE_BIBLE.md](VENUE_BIBLE.md) | 场地圣经模板（轴线 / 机位 / 灯光） |
| [PROMPTS.md](PROMPTS.md) | H3 提示词骨架（Emotion / 运镜 / Continuity） |
| [APPLY.md](APPLY.md) | 新片怎么挂到本 playbook |

## 硬规则（全项目）

- **任何视频生成前**须 wen hao 明确同意（金融视频组批量例外且当前暂停另计）。  
- 人物主镜默认 **fl2va**；**禁止**新开 ref2va 人物主镜（气氛空镜可 first_only）。  
- 首尾帧 5 项未过 → **禁止**入 GPU 队列。  
- 成片统一调色放最后；中间禁止各 batch 各玩一套 LUT。

## 与脚手架的关系

本仓原有 `align → storyboard → preview` 仍是轻量预览层。Playbook 管的是 **上 H3 / 实拍级成片** 时的纪律；预览通过 ≠ 可以烧 GPU。
