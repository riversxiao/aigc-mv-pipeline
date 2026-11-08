# 工程目录约定

每个片子一个 `projects/<project_id>/`，playbook 本身不含大媒体。

```
projects/<project_id>/
  README.md                 # 片名、曲目、状态、Drive 链接
  brief.yaml                # 可选：接 aigc-mv CLI
  cast/                     # 定妆：MICW / QuadView / portrait
  venue/                    # Venue Bible：平面图 + A/B/C/D + 灯光版
  audio/                    # song.wav 等
  config/
    timing.json             # sections / 总帧
    board.json              # 分镜
    h3_assets*.json         # 角色 portrait 引用
  keys/                     # <shot_id>_a.png / _b.png
  edit/
    keyframe_qc/            # 硬检记录
    edl.json                # 成片 EDL
  renders/                  # GPU 产出（可 gitignore）
  docs/
    GAP_vs_ref.md           # rea-video 差距（可选）
```

仓库根目录：

```
playbook/                   # 本通用纪律（本目录）
knowledge/                  # 跨片可复用 canon / lore（酒楼诗人等）
projects/                   # 各 IP / 各集挂载点
```

大文件、母带、GPU 缓存：**不要**提交到 Git；用 Drive / 对象存储，在项目 README 写链接。
