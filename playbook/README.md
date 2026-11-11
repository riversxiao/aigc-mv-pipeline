# Playbook · 跨项目制片纪律（`rea-video` + H3 双轨制版）

本目录将「焚诀」七步纪律、《火影有嘻哈 EP03》`rea-video` 拉片基准，以及《异人开麦 ep03：三重修在心里面》`v3 → v6` 四轮实战消融验证后的**可复用编排流程**沉淀下来，供：

- **一人之下**（`projects/yirenzhixia/`，含《雷有两面》、《罗天大醮有嘻哈》等 MV）
- **世界名人大乱斗 / 异人开麦**（`projects/world_celebrity_battle/`，含 `ep03` 陆瑾 VS 李慕玄等）
- 酒楼诗人及其他历史/国漫说唱对决新片

共用同一套门禁；**角色、场地、曲目只挂在各自 `projects/<id>/`**。

上游方法融合：
- [MinLiBuilds「焚诀」/ copy-kakasi](https://github.com/limin112/min-skill/tree/main/skills/copy-kakasi)（先剪后拆、多角度定妆、静帧硬检、统一终调色）
- [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video)（参考片定量拆解 + 成片 `still_motion` / 运镜 / 跳切闭环审计）
- 《异人开麦 ep03》`v6` H3 双轨制（彻底解决单张立绘 `fl2va` 锁死第 0 帧导致的手势僵死与静帧感）

## 一句话核心经验

成片出现「像 PPT 静帧、手势全程不变、切镜突兀」三大顽疾，根因不是提示词少了几个修饰词，而是必须守住以下四步：

1. **先锁母带与节拍再分镜**：以原始母带唯一时长与分轨（`vocals` / `drums` / `other`）锁死时间轴，器乐切镜按分轨真实入点落刀并由本片角色实景演奏（严禁悬空双手）。  
2. **三步多角度定妆 + 官方底图 `img2img` 群像**：主角拼 `3:2` 五视图组图（`_sheet.png`）；观众与客串反应一律基于已有定妆/官方底图做 `img2img`，禁纯文生图捏路人。  
3. **H3 双轨制生成路由（取代旧版一刀切 `fl2va`）**：
   - **主唱说唱/副歌默认走 `ref2va_pose`**（`[角色_sheet, 舞台空镜]` + 去面部 21 点 `DWPose` `0.72@0.84` + `H3LockGuideAudio` + 六层生物力学多拍手势）；
   - **武术/炁浪/器乐/观众反应默认走 `ref2va_depth`**（`ControlNet Depth` `0.68@0.82` 三层视差 + 两拍微表情转折）；
   - **跨年龄/状态蜕变专走 `fl2va_morph`**（`_a.png → _b.png` 首尾姿态必须显著不同；**严禁把同一张静态肖像当首帧重复喂给多个说唱镜头**）。  
4. **`rea-video` 闭环门禁 + 24fps Battle-HUD + 统一终调色**：跑 `aigc-mv ep rea-audit --check-flow` 达标（`still_motion <= 3%`、动态机位 `>= 90%`、`jump <= 1`、中位位移 `>= 0.12px`）后再统一调色出片。

## 文档索引

| 文件 | 用途 |
|---|---|
| [PIPELINE.md](PIPELINE.md) | 八步闭环流水线 + P0/P1 优先级 + H3 双轨路由表 |
| [SHOT_LIST_TEMPLATE.md](SHOT_LIST_TEMPLATE.md) | 挂点 / 分镜表模板（含 `h3_mode`、ControlNet 与空间递进自检） |
| [KEYFRAME_QC.md](KEYFRAME_QC.md) | 定妆组图 / 双关键帧 / ControlNet 控制视频硬检 Checklist |
| [DIRECTORY.md](DIRECTORY.md) | 工程目录约定 |
| [VENUE_BIBLE.md](VENUE_BIBLE.md) | 场地圣经模板（轴线 / 四阶空间调度 / 灭灯追光 cue） |
| [PROMPTS.md](PROMPTS.md) | H3 六层生物力学动作解耦提示词骨架（多拍手势 + 声腔口型规则） |
| [APPLY.md](APPLY.md) | 新片怎么挂到本 playbook |
| [../docs/火影有嘻哈_rea_video拉片与ep03实战演进.md](../docs/火影有嘻哈_rea_video拉片与ep03实战演进.md) | 《火影有嘻哈》`rea-video` 拉片数据与 `ep03 v3→v6` 完整消融报告 |

## 硬规则（全项目）

- **任何付费/GPU 视频生成前**须明确审批（`aigc-mv ep approve` + 预算闸门）；失败镜头同一方法最多尝试 **2 次**，超限立即切换路由或改用库内合格素材，空闲 GPU 实例及时关闭。  
- **禁止单张静态立绘重复走 `fl2va` 拍说唱主镜**（必触发锁首帧静帧感）；`fl2va` 仅用于首尾姿态经校验显著不同的跨龄/状态变身或起落幅转场。  
- **禁止声画错位与悬空肢体**：男女声部、苍老/青年声线必须与画面角色 100% 对应；鼻音「哼」及听句方全程闭口；击鼓抚琴必见角色半身/全身。  
- **成片必过 `ep rea-audit` 门禁**，字幕优先启用 `battle_hud` / 24fps 动态卡拉 OK + 阵营印章，全片最后只做**一次**统一胶片调色。
