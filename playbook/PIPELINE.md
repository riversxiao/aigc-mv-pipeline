# 八步闭环流水线（焚诀 × 《火影有嘻哈》`rea-video` × H3 双轨制）

适用：一人之下 MV、世界名人大乱斗 / 异人开麦、酒楼诗人等写实说唱对决与叙事 MV。

| # | 步骤 | 过关标准 | 常见缺口与反模式 |
|---|---|---|---|
| 1 | **锁母带与四阶分镜** | 唯一母带时长 + 分轨（`vocals/drums/other`）；`ep board` 含四阶空间递进（分立 OTS → 5cm 贴脸 → 下台护栏互动 → 灭灯单束追光）与 ≥25% 反应/器乐切镜 | 不看分轨盲切鼓点；全程单人正面站桩 |
| 2 | **三步定妆 + 图生图群像** | 主角齐备 `face/34/profile/half/full` 拼 `3:2` `_sheet.png`；观众/评委反应由已有定妆/官方底图 `img2img` 派生 | 单张正面图闯天下；纯文生图随机捏路人观众 |
| 3 | **双轨控制源准备** | `ref2va_pose` 备妥去面部 21 点 `DWPose` 骨骼视频；`ref2va_depth` 备妥三层景深视频；`fl2va_morph` 备妥首尾姿态显著不同的 `_a.png` + `_b.png` | 同一张静态肖像当首帧喂十几个 `fl2va` 镜头 |
| 4 | **入队前五项硬检** | 见 [KEYFRAME_QC.md](KEYFRAME_QC.md)；角色发色/服装红线、左右手、骨骼去脸点、`end_percent<=0.86` 全部核对 | 带面部关键点锁死高音嘴型；`end_percent=1.0` 渗出灰雾/线条 |
| 5 | **六层生物力学提示词** | 见 [PROMPTS.md](PROMPTS.md)；含重心转移 + 空闲手「进画—出画—再抬手」多拍切换 + 高音大开颌/鼻音闭口规则 | 套话「跟着节奏比划」导致单手悬空微抖 |
| 6 | **H3 双轨生成与口型对齐** | 按 `units/<id>/request.json` 的 `h3_routing` 执行；同方法失败 ≤2 次；跑 `ep sync` 校验口型延迟 `< 40ms` | 整批盲跑不测延迟；失败镜头无限重试烧算力 |
| 7 | **Battle-HUD 包装与终调色** | `subtitle_style: battle_hud`（阵营印章 + 24fps 逐字能量推进 + 毛笔重音尾字 `1.24x` 放大 + 典故胶囊）+ 全片一次性胶片调色 | 白字平铺无重音层次；各批次分头套 LUT |
| 8 | **`rea-video` 闭环质检** | `aigc-mv ep rea-audit <ep> --check-flow --strict` 全绿：`still_motion <= 3%`、移动+手持 `>= 90%`、`jump <= 1`、位移 `>= 0.12px` | 不做客观动态审计直接交付，遗留「1分03秒式静帧」 |

## H3 双轨路由速查（`cinema.select_h3_route` 自动写入 `request.json`）

| `h3_mode` | 适用单元 / 调度 | 输入组合 | ControlNet 参数 | 解决的核心痛点 |
|---|---|---|---|---|
| **`ref2va_pose`** | 主歌说唱、高音副歌、主持串词（默认 `sung`） | `角色_sheet.png` + `venue.png` | `DWPose`（21 点去脸）`strength=0.72, end=0.84` + `H3LockGuideAudio` | 消除单图 `fl2va` 锁首帧静帧感，释放躯干压步、多拍手势与高音大嘴型 |
| **`ref2va_depth`** | 武术招式、炁浪、实景角色击鼓抚琴、观众/评委两拍反应（默认 `motion`） | `角色/群像图.png` + `venue.png` | `Depth Anything V2` `strength=0.68, end=0.82`（无口型） | 赋予三层空间视差与真实运镜推拉，杜绝平面图片 Ken Burns 感与灰雾渗色 |
| **`fl2va_morph`** | 老年→少年跨龄变身、灭灯追光揭晓、升空化白炁（`morph_transition`） | `keys/<id>_a.png` + `keys/<id>_b.png` | 双关键帧首尾锚定（姿态 L1 差 `>= 0.06`） | 精准控制跨年龄/跨形态连续蜕变，首尾构图严丝合缝 |

## 镜头时长与节奏甜区

- **对标《火影有嘻哈 EP03》**：约 `92–98 BPM` 曲目平均镜长控制在 **`2.2s–3.4s`**（高燃双倍速段落可收至 `1.8s–2.4s`），单镜最短不低于 `0.8s`（送 H3 原生生成建议 `>= 2.0s` 再按音乐拍点精剪）。
- **连续同唱者防跳切**：相邻两镜若仍为同一唱者，景别必须跨两档（如 `MS → ECU`）或切 `ots_hair` / `faceoff_profile` / 2 拍听者反应镜，确保全片 `jump <= 1`。

## 参考

- 拉片与消融详解：[../docs/火影有嘻哈_rea_video拉片与ep03实战演进.md](../docs/火影有嘻哈_rea_video拉片与ep03实战演进.md)
- 拉片工具：[JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video)（集成入口：`aigc-mv ep rea-audit`）
- 上游纪律灵感：[copy-kakasi](https://github.com/limin112/min-skill/tree/main/skills/copy-kakasi)
