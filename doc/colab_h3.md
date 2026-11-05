# 在 Google Colab 里用 MiniMax H3 做视频

这份说明告诉你（和 Colab 里的 agent）这个包里哪些文件是做视频要用的、怎么在 Colab 里拿到它们。
MiniMax H3 的接口参数（模型名、参考图字段、音频字段、时长上限、价格）请以 MiniMax 官方文档为准，这里不替它写。

## 1. 在 Colab 里拿到素材

```python
!git clone -b handoff --single-branch --depth 1 https://github.com/riversxiao/aigc-mv-pipeline.git handoff
%cd handoff
!pip -q install soundfile numpy
!python tools/restore_audio.py projects/wangye_vs_zhugeqing   # 还原 audio/song.wav、vocals.wav、instrumental.wav
!sha256sum -c SHA256SUMS | grep -v ': OK' || echo 全部校验通过
```

如果还要跑我们的剪辑流水线（对口型测量、拼成片、字幕），再拉代码分支：

```python
!git clone -b feat/cinematic-battle-pipeline --depth 1 https://github.com/riversxiao/aigc-mv-pipeline.git code
!cp -r handoff/projects/wangye_vs_zhugeqing/. code/projects/wangye_vs_zhugeqing/
%cd code
!pip -q install -e ".[dev]"
```

## 2. 一张表看懂每个镜头：`projects/wangye_vs_zhugeqing/shots.csv`

72 行，一行一个镜头，按时间顺序。`shots.json` 是同样内容的 JSON。

| 列 | 含义 |
| --- | --- |
| `shot` | 镜头编号 s001–s072 |
| `t0` / `t1` / `dur` | 在歌里的起止秒数和时长 |
| `section` / `kind` | 段落（主持、副歌、诸葛青主歌、王也主歌、揭晓、结尾）和镜头类型（唱、反应、观众、评委……） |
| `who` / `who_cn` | 画面里的人（角色键和中文名） |
| `singer` / `lip_sync` | 谁在唱；`yes` 表示这个镜头要对口型 |
| `lyric` | 这个镜头里唱的歌词 |
| `framing` / `lens` / `camera` | 景别（CU/MCU/MS/WS…）、镜头焦段、运镜 |
| `staging` / `action_cn` | 站位类型、画面动作（中文，可直接写进提示词） |
| `unit` / `unit_song_t0` / `unit_duration` / `unit_audio` | 原来给即梦的生成单元编号、单元在歌里的起点和时长、用的是人声还是伴奏 |
| `dreamina_take` | 已经用即梦生成好的视频（29 段，覆盖 55 个镜头）；空着的就是还没有视频的镜头 |
| `ref_images` | 建议上传的参考图：这个人的正面定妆照，加一张和景别匹配的角度图（近景用半身 `_half`，远一些用四分之三侧 `_34`） |

还没有视频的 17 个镜头在 `dreamina_take` 为空的行里，对应单元 u01–u04、u32–u38、u41–u44（开场、主持、副歌回归、结尾互动、片尾）。只补这些就能凑齐整期。

## 3. 每类素材在哪

- 人物参考图 `refs/`：15 个角色，每人 6 张，全部是 AI 生成图（不含官方原作图）：
  - `<key>_face.png` 正面定妆照
  - `<key>_34.png` 四分之三侧、`<key>_profile.png` 侧面
  - `<key>_half.png` 半身（唱歌和主持的人拿着话筒）、`<key>_full.png` 全身
  - `<key>_sheet.png` 以上拼成的一张定妆组图
- 场景图 `refs/`：`venue`（舞台正面）、`venue_high`（高位全景）、`venue_dark`（灭灯）、`crowd`、`crowd_reverse`、`cameo_seats`、`judges`、`dj_booth`、`hook_mics`。
- 角色键对照：`a` 诸葛青、`b` 王也，其余见 `episode.yaml` 的 `cast`。
- 音频：
  - 整首歌和两条分轨：还原后在 `audio/`（`song.wav` 整曲、`vocals.wav` 主唱干声、`instrumental.wav` 伴奏），48 kHz 立体声。
  - 每个单元已经切好的音频窗口：`units/<编号>/<编号>_vocal.wav`（唱段，人声前留了 0.3 秒静音）或 `_inst.wav`（伴奏）。
- 逐字时间：`analysis/timing.json` 的 `lines[]`，每句有 `t0`/`t1`、半句 `phrases[]` 和每个字的起点 `chars[]`。
- 原来给即梦写的提示词：`units/<编号>/prompt.txt`（中文，剧本式，每半句写了秒数）。H3 可以参考里面的人物、动作和画面描述，但格式要按 H3 的要求改。
- 已生成的即梦视频：`units/<编号>/takes/take-1.mp4`，29 段，720p。

## 4. 用 H3 做的建议（来自之前的踩坑记录，不是 H3 官方要求）

- 一条只给一句歌词：一条里放两句时，模型常在第二句自己重唱，嘴对不上。音频按 `timing.json` 里这一句的 `t0`–`t1` 切，前面留 0.3 秒静音。
- 近景用半身图 `_half.png` 当参考，不要用全身图：用全身图容易拍成远景，脸太小看不清口型。
- 唱的人用 3/4 侧脸，话筒拿低一点，不要挡住嘴。
- 站位固定：诸葛青在画面左边，王也在右边。
- 生成后把视频的音轨换回原歌，画面按 `t0` 摆回时间线上；我们的流水线 `aigc-mv ep ingest-takes` 和 `ep render --res 1080p` 能自动做这一步（把视频放到 `units/<编号>/takes/take-N.mp4`）。

## 5. 版权和隐私

- 《一人之下》同人二创，仅供娱乐；角色全部是成年人；脸是原创的，不像任何真人演员。
- 这个仓库是公开的，包里的歌和角色图任何人都能下载。用完可以让我删掉这个分支。
