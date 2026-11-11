# 分镜 / 挂点表模板（焚诀 × 《火影有嘻哈》四阶调度 × H3 双轨版）

片：____________________  曲：`song.wav`（唯一母带基准：______ s @ 24fps）  
对标插空/反应比：≥25%（参考片约 30%）  `rea-video` 门禁：`still_motion <= 3%` · 动态机位 `>= 90%` · `jump <= 1`

## A. 挂点与分轨入点表（Beat & Stem Map）

从 `analysis/timing.json` 与分轨（`vocals.wav` / `drums.wav` / `other.wav`）核对填入；鼓、琴等器乐切镜必须精确对齐分轨真实瞬态入点。

| beat_id | tc_in | tc_out | section | 空间阶梯 | 必出景别/调度 | 声部与角色核对 | 分轨备注 |
|---|---:|---:|---|---|---|---|---|
| B01 | 0.00 |  | cold_open | 立轴揭幕 | WS + `instrument_stage` | 实景角色奏乐（禁悬空手） | 对齐 `drums`/`other` 起音 |
| B02 |  |  | entrance / morph | 跨龄入场 | MCU `morph_transition` | 老变少双关键帧蜕变 | 剪除多余念白废句 |
| B03 |  |  | verse 1 | 第一阶：分立正反打 | MCU / OTS / CU | 男/女声线核对无串唱 | 空闲手 2–3 拍进出画 |
| B04 |  |  | hook / verse 2 | 第二/三阶：5cm贴脸 + 下台护栏 | 2S `faceoff_profile` / `barrier_interact` | 高音大开颌；听者闭口 | 穿插 `img2img` 观众两拍反应 |
| B05 |  |  | reveal / outro | 第四阶：瞬灭单束追光 | WS `blackout_spot` → CU `spot_cu` | 鼻音「哼」保持闭口 | 宗师升空/白炁三重残影 |

## B. 分镜与 H3 双轨路由表（Shot List）

一行一镜，`shot_id` 终身不变；同方法失败最多重试 **2 次**。

| shot_id | tc_in–out | 景别/焦段 | 运镜 | 角色与声部 | `h3_mode` | 参考图 / 首尾帧 | ControlNet (`strength@end`) | 入队QC | 光流(px) | 状态 |
|---|---|---|---|---|---|---|---|---|---:|---|
| S001 |  | WS / 35 | push_slow |  | `ref2va_depth` | `venue.png` + `crowd.png` | `depth 0.68@0.82` | ☐ |  | 草稿 |
| S002 |  | MCU / 50 | push_slow | 老→少变身 | `fl2va_morph` | `keys/S002_a.png` → `_b.png` | `dual_keyframe` | ☐ |  | 草稿 |
| S003 |  | MCU / 85 | tele_float | 主唱 A | `ref2va_pose` | `a_sheet.png` + `venue.png` | `pose_no_face 0.72@0.84` | ☐ |  | 草稿 |

状态枚举：`草稿` → `挂点确认` → `控制源就绪` → `QC通过` → `排队` → `已出片` → `rea-audit通过` / `返修`

## C. 《火影有嘻哈》编排配额与防尬自检

| 检查项 | 门禁目标 | 本表实测 | 达标 |
|---|---|---:|---|
| 反应 + 器乐 + 群像切镜占比 | `>= 25%` 镜数或时长（观众一律 `img2img`） |  | ☐ |
| 主力景别种类（占比 `>= 5%`） | `>= 3` 类（MS / MCU / CU / WS 交替，连续同唱者必换两档景别） |  | ☐ |
| 四阶空间递进 | 含 `ots_hair` + `faceoff_profile` + 观众互动 + 全片唯一 1 次 `blackout_spot` |  | ☐ |
| 声画与嘴型核对 | 0 处男女声串唱、高音大开颌、鼻音「哼」与听者 100% 闭口 |  | ☐ |
| `ep rea-audit --check-flow` | `still_motion <= 3%`、`moving >= 90%`、`jump <= 1`、`flow >= 0.12px` |  | ☐ |

## D. `rea-audit` 靶向返修清单（自动生成自 `edit/rea_audit.md`）

| shot_id | 时间段 | `rea-video` 分类 / 位移 | 根因诊断 | H3 返修处方（`ref2va_pose` / `ref2va_depth` / 插入反应镜） |
|---|---|---|---|---|
|  |  |  |  |  |
