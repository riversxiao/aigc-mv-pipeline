# 骨骼素材库交接接口

本文供负责骨骼提取素材库的 agent 使用。素材库负责片段提取、骨骼质量检查和索引；
本项目负责按角色选动作、逐镜提示词、时长适配和 H3 任务编译。不要为对接而重新生成视频。

## 最小交付

交付一个本地目录或可完整下载的压缩包，包含 JSON 索引、索引引用的骨骼视频以及来源说明。
告诉我索引文件的实际路径；如果已有其他格式的索引，保留原格式，提供字段说明即可映射。

建议的目录：

```text
motion_library/
  catalog.json
  clips/
    rap_small_downbeat_v1.mp4
  previews/                     # 可选：原动作与骨骼同屏预览
```

索引的最小适配格式如下。这里是占位示例，不是已经存在的素材；未完成检查时保留 `pending`。

```json
{
  "schema_version": 1,
  "motions": {
    "rap.small_downbeat.v1": {
      "kind": "pose_video",
      "status": "pending",
      "people": 1,
      "path": "clips/rap_small_downbeat_v1.mp4",
      "sha256": null,
      "microphone_hand": "right",
      "framings": ["MCU", "MS"],
      "views": ["front", "three_quarter"],
      "source_url": "",
      "source_interval_seconds": [0, 0],
      "description": "",
      "pose_format": "",
      "bpm": null,
      "tags": ["restrained", "downbeat", "settle"]
    }
  }
}
```

`motions` 的键是稳定版本 ID。`path` 相对索引目录，不能逃出该目录。
文件实际存在、可解码、SHA256 正确且人工检查完成后才将 `status` 改为 `ready`。
同一 ID 的字节不要覆盖，修改动作使用新版本。

## 素材要求

- 提供去外观的骨骼视频；当前接法需要一个明确的目标人物。多人原片先分离、跟踪目标人物。
- 骨骼视频无音轨，不烧录字幕、标题或来源水印。来源放在索引与预览中。
- 原始帧率和时长可以保留，文件需带正常时间戳和时长元数据。每个使用区间不超过 15 秒，
  单文件不超过 200 MiB。这里是适配器的处理限制，不是对所有生成模型的能力声明。
- 标注适用景别与视角：`front`、`three_quarter`、`profile`、`back`。不要把半身动作标成全身可用。
- `microphone_hand` 使用 `left` / `right` / `none`；`either` 仅用于确实不受持麦手约束的通用动作。
  不要用它掩盖镜像或左右手不匹配。
- 保留准备、重音动作、收势和停顿，检查手腕跳变、左右互换、遮挡时误认、出入画和切镜。
  `ready` 表示素材检查完成，不表示某个角色的最终画面已通过验收。

角色方向：王也偏松弛、克制、低幅动作；诸葛青偏从容、精准、干净落点。
这是选材方向，不必把所有动作都绑定到特定角色；同类动作可以跨角色、跨集复用。

## 本项目如何使用

`h3_assets.json` 中：

```json
{
  "schema_version": 4,
  "directing_plan": "direction.json",
  "motion_library": "../../libraries/motions/catalog.json"
}
```

每镜 `direction.json` 的绑定：

```json
{
  "motion": {
    "required": true,
    "asset_id": "rap.small_downbeat.v1",
    "fit": "retime",
    "start": 0,
    "end": null
  }
}
```

导出时仅调整动作视频：将选定区间适配到本镜演唱窗口，补齐前导与结尾停顿，
输出 H3 合法帧数的 24 fps 无声视频。`retime` 的动作速度限制在 0.5–2 倍；
`trim_hold` 按正常速度截取、短缺处保持尾姿。歌曲与目标干声保持原时钟。
需要精确踩拍的片段仍要审阅，自动等比例适配不等于自动理解每个音乐重音。

预检会核对角色、景别、视角、持麦手、文件和哈希；索引没到、素材待检查或镜头未选动作时明确报待完成。
无需提前填假路径、假哈希或假审核记录。素材库就绪后进行接入检查，不会因此自动开 GPU。
