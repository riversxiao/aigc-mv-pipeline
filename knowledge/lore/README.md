# 典故卡 · Lore cards

每张 YAML 是一首 MV 的**剧情 + 歌词背景**：取《史记》《左传》等经典故事，做**借古讽今**，映射到当代非政治话题（职场信用、友情信任、长期主义、手艺、名声、金钱与承诺等）。

## 创作铁律

- **借古讽今，但不讽刺政治。** `avoid` 字段必须包含与政治讽刺相关的条目。
- `classic_summary` 只写中性历史本事，不影射当代政局。
- `modern_allegory` 明确落到人情、工作、手艺、名利观等可唱话题。
- `lyric_seeds` / `scene_beats` 要适合酒楼开麦 MV（舞台、灯火、旧友、承诺、熬夜练功等画面）。

## 字段说明

| 字段 | 含义 |
|------|------|
| `id` | 文件名 stem，如 `guan_bao_zhi_jiao` |
| `source` | 出处，如 `史记` / `左传` |
| `classic_title` | 典故名 |
| `classic_summary` | 短中性本事 |
| `modern_allegory` | 借古讽今角度（非政治） |
| `themes` | 主题词列表 |
| `lyric_seeds` | 可直接改写成歌词的短句种子 |
| `scene_beats` | 分镜动作提示 |
| `avoid` | 禁区（须含政治讽刺类） |
| `notes` | 可选备注 |

## CLI

```bash
aigc-mv list-lore
aigc-mv get-lore guan_bao_zhi_jiao
aigc-mv lyric-brief guan_bao_zhi_jiao
```

项目 `brief.yaml` 里写 `lore_id: guan_bao_zhi_jiao`，`storyboard` 会把 allegory / themes 轻量注入镜头 action 与 plate prompt。
