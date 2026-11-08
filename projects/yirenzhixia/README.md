# 一人之下 · 项目挂载

套用仓库根目录 [`playbook/`](../../playbook/)。

## 范围

- MV / 擂台类短片，例如《雷有两面》、综艺向《罗天大醮有嘻哈》等。
- 仓库里已有一期示例工程：[`../wangye_vs_zhugeqing`](../wangye_vs_zhugeqing/)（诸葛青 VS 王也，`format: show`）。**本目录是 IP 级索引 + 焚诀门禁说明**；具体一期仍用 `projects/<一期>/` 的 episode 结构。

## 与 playbook 的接法

| Playbook 步骤 | 本仓 CLI / 目录 |
|---|---|
| 先剪后拆 | `aigc-mv ep board` → `board/board.md` 确认后再花钱 |
| 定妆多角度 | `ep refs` 三步定妆 + `ep sheets` 组图 |
| 首尾帧 / 硬检 | 见 `playbook/KEYFRAME_QC.md`；静帧过检后再生成 |
| fl2va 优先 | 人物主镜默认 fl2va；禁 ref2va（气氛空镜可 first_only） |
| Venue Bible | `refs/venue.png` + 文字规则；复杂场地另建 `venue/` |

## 外部大工程（未整包入库）

- 本机 `/workspace/films/luotian_ep02_v10_plan/` — 《雷有两面》ep02 焚诀案、Venue Bible、rea-video 差距  
- Drive 成片 / 场地圣经链接写在各期 README，不进 Git

## 开下一集检查单

- [ ] 挂点 / 分镜表确认（board 审核 PASS）  
- [ ] 主创定妆 sheet 齐套  
- [ ] 场地轴线与灯光 cue 锁定  
- [ ] 首尾帧硬检  
- [ ] wen hao 批准后再提交生成 / 烧 GPU
