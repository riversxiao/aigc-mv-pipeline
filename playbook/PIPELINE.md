# 七步流水线（焚诀对齐 · 通用版）

适用：一人之下 MV、世界名人大乱斗 / 异人开麦、酒楼诗人等。

| # | 步骤 | 过关标准 | 常见缺口 |
|---|---|---|---|
| 1 | **先剪后拆** | 有挂点表 + 分镜预览（可用静帧），用户确认后再排队 GPU | 整表生成后再 remix |
| 2 | **定妆多角度** | 主创有 face/hair/outfit/body；建议 MICW 16:9 + QuadView | 只有单张正面 portrait |
| 3 | **每镜首尾帧** | `keys/<shot_id>_a.png` + `_b.png`；气氛空镜可 first_only | 单关键帧 I2V |
| 4 | **静帧硬检** | 见 [KEYFRAME_QC.md](KEYFRAME_QC.md)；Fail 不入队 | 只在成片 take 上评审 |
| 5 | **提示词** | Emotion + 动作方向 + 运镜 + Continuity；禁堆 8K/cinematic 词 | 套话「单一主动作…」 |
| 6 | **最后才视频** | 默认 **fl2va**；单镜 `--redo`；人物主镜禁 ref2va | 整 batch 一把梭 |
| 7 | **统一收尾** | 字幕/包装后统一 grade（LUT/轻微颗粒/色温） | 多 batch 光源各异 |

## 优先级

### P0（开干前必须，可不烧 GPU）

1. 填 [SHOT_LIST_TEMPLATE.md](SHOT_LIST_TEMPLATE.md)；插空 / Insert 目标 ≥25% 镜数或时长。  
2. Manifest 字段：`first_frame` / `last_frame` / `h3_mode=fl2va`。  
3. 上线首尾帧硬检；不过检不入队。

### P1（有静帧产能；GPU 须明确授权）

4. 主创多角度 sheet → 写入项目 `cast/`。  
5. 2–3 镜 fl2va A/B（同 seed 记录），验证口型。  
6. 提示词改 Emotion 模板。  
7. assemble 增加可选 grade（默认关）。

### P2

8. 服务器侧 prepare/collect。  
9. 静帧确认页（类 review 画布）。  
10. 身份包版本号（OmniChar / `.char` 等）与 sheet 打通。

## 镜头时长

尽量 ≥1.5s 再送 H3；更短镜可生成长再 speed 压回，避免动作畸变。

## 参考

- Skill 原文：[copy-kakasi](https://github.com/limin112/min-skill/tree/main/skills/copy-kakasi)  
- 拉片工具：本机 `rea-video`（对照参考片出差距清单后再改分镜）
