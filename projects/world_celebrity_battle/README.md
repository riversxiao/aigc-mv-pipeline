# 世界名人大乱斗 / 异人开麦 · 项目挂载

套用仓库根目录 [`playbook/`](../../playbook/) 与 [《火影有嘻哈》rea-video 拉片与 ep03 实战演进](../../docs/火影有嘻哈_rea_video拉片与ep03实战演进.md)。

## 范围

- 擂台对决、说唱 / 开麦类短片（代表作：《异人开麦 ep03：三重修在心里面》陆瑾 VS 李慕玄）。
- 与「一人之下」共用同一套：先剪后生成、三步定妆、**H3 双轨制生成（`ref2va_pose` / `ref2va_depth` / `fl2va_morph`）**、六层生物力学手势、Battle-HUD 动态字幕与 `rea-video` 闭环门禁。

## 已入库角色与功法知识卡

- 角色卡（`knowledge/characters/`）：`lu_jin.yaml`（陆瑾）、`li_muxuan.yaml`（李慕玄）、`lu_linglong.yaml`（陆玲珑，粉发鹤氅副歌主唱 / 擂鼓手）、`zuo_ruotong.yaml`（左若童，大盈仙人）
- 功法典故卡（`knowledge/lore/`）：`nisheng_sanchong.yaml`（逆生三重）、`tongtianlu.yaml`（通天箓）

## 已完成实战标杆：《异人开麦 ep03：三重修在心里面》（v6 终版）

- **音频唯一时间基准**：原始 Suno 母带 `179.160s`（原速原词，人声 / 鼓 / 琴分轨锁帧对齐）
- **`rea-video` 对标《火影有嘻哈 EP03》实测指标（`v3 → v4 → v5 → v6`）**：
  - `still_motion` 静图推拉占比：`13.8% (v4)` → `10.0% (v5)` → **`2.2% (v6)`**（优于阈值 `<= 3.0%`）
  - 移动 + 手持动态机位占比：`73.6% (v4)` → `82.6% (v5)` → **`97.0% (v6)`**（对标《火影有嘻哈》`100%`）
  - 同机位跳切 `jump`：`7 处 (v3)` → `3 处 (v4)` → **`1 处 (v6)`**（与《火影有嘻哈》持平）
  - 重制段落平均光流位移：`0.306 px` → **`1.078 px`（提升 `3.52x`）**
- **云端交付归档（大媒体不进 Git）**：
  - Google Drive 交付目录：https://drive.google.com/drive/folders/1P7cBX3CVyd4XQZEM9df1a0A7KIfqYRYc
  - 原始素材目录：https://drive.google.com/drive/folders/1CEjo6r9kjEVC1SuCQ-pUU9y4RlZGBzUU
  - 原始 Suno 母带（`179.160s`）：https://drive.google.com/file/d/1IkQiM__bcOmrVH8qpW28q8xbdSQS-a-V/view

## 与《火影有嘻哈》对标核心铁律

经 `rea-video` 全片 67 镜逐镜复核（`shot_001` 片头明确标注 `LibTV` 生成，`still_motion` 仅 `0.8%`），禁止再对普通说唱镜头使用单张静态图 `fl2va`（会导致锁首帧身体僵死）：

1. **主唱对口型一律 `ref2va_pose`**：定妆组图 + 舞台空镜 + 去面部关键点的 21 点 DWPose 骨骼（`0.72@0.84`）+ `H3LockGuideAudio` + 单镜多拍空手出入画。
2. **动作 / 器乐 / 群像一律 `ref2va_depth`**：三层深度视差（`0.68@0.82`）；器乐必须由角色本人演奏，观众席优先用已有剧照 `img2img` 图生图。
3. **`fl2va_morph` 仅限跨年龄 / 化气变身**：起止关键帧姿态必须显著不同（如老年陆瑾 / 李慕玄返少年）。

## 开一期检查单

- [ ] 主对决双方与副歌歌手定妆组图齐套（发色、服饰红线写进角色卡 `forbidden`）
- [ ] 场地 / 擂台 Venue Bible（左右站位轴线固定，器乐归属角色明确）
- [ ] 分镜挂点 + 反应 / 观众 `img2img` 配额 + `subtitle_style: battle_hud`
- [ ] 首帧硬检通过 + 预算门禁批准后再烧 G4 GPU
- [ ] 粗剪跑 `aigc-mv ep rea-audit --check-flow --strict` 全绿后封母带

