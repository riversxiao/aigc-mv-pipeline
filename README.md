# aigc-mv-pipeline

**CN**｜做「像真人实拍」的 AI 说唱对决 / 音乐视频的流水线：Suno 做歌 → 节拍和逐字时间 → 按镜头语言自动分镜 → 即梦 Seedance 提示词（口型按半句写秒数）→ 生成后逐条测量口型延迟 → 按帧对齐剪辑、逐镜头调色、字幕和史料注释。

**EN**｜A pipeline for photoreal AI rap battles and music videos: song timing, a film-language storyboard with an audit, script-style Seedance prompts with timed half-lines, per-take lip-sync measurement, and a frame-exact graded conform.

方法来源：[claudia.gallery](https://claudia.gallery/) 的制作记录（节拍分镜、人声 stem 口型、花钱闸门、逐镜头调色）、[ancient-rap-battle](https://github.com/10291124jcjc-dotcom/ancient-rap-battle)（按半句写秒数、固定站位、史料注释），以及两支参考片的镜头语言：Keynes vs Hayek《Fear the Boom and Bust》（广角贴脸、对手同框、真实场景）和《火影有嘻哈》（综艺长焦机位、反应镜头）。每条规则的来由见 [docs/方法论.md](docs/方法论.md)。

## 相比原版改了什么

| 问题 | 改法 |
| --- | --- |
| 真人感弱、脸像网红 | 角色卡写明确年龄、皮肤瑕疵、胡茬、疤；`REALISM_CN` 写进每条提示词；审核拦截「唯美 / 帅气 / 8k / masterpiece」这类词；参考图缩到输出分辨率；不用 AI 放大 |
| AI 感强、像 CG | 光必须来自画面里的真实光源；正常速度、有重量的动作；后期逐镜头拉齐曝光和白平衡，再加一层胶片曲线、泛光和颗粒，不锐化 |
| 运镜差、重复 | 16 种运镜，每个镜头一个，有起幅和落幅，运镜从重拍开始；同一运镜不连用，稀有运镜有全片上限；长焦和广角按语法交替 |
| 只有两个人站着唱 | 每四句一个对手反应镜头；`cutaway:` 把典故拍成叙事插入；开场摇臂、间奏观众、片尾输赢 |
| 口型 | 用 Suno 人声 stem 切窗口（首字前 0.3 秒，单元外的字静音），4–8 秒一单元；生成后测每条的延迟和跟丢位置，剪辑按测量结果放画面 |
| 花钱失控 | 不批准不提交，提示词一改就要重新批准；预算上限、总开关、账本 |

## 快速开始

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"            # 核心：numpy / soundfile / pillow / imageio-ffmpeg（自带 ffmpeg）
pip install -e ".[asr]"            # 可选：faster-whisper + pypinyin，用真实人声做逐字对齐

E=projects/xiangyu_vs_liubang       # 示例一期：项羽 vs 刘邦

aigc-mv ep suno $E                  # suno.md：两段生成 + Extend 的风格和歌词栏
# 把 Suno 的歌、人声 stem、伴奏 stem 放进 $E/audio/（song.wav / vocals.wav / instrumental.wav）
aigc-mv ep analyze $E               # 节拍、每句和每半句的时间 → analysis/timing.json
#   还没有歌时：aigc-mv ep analyze $E --bpm 92   （用合成节拍网格先做分镜）
aigc-mv ep board $E                 # 分镜 + 生成单元 + 审核 → board/board.md（给导演看）
aigc-mv ep refs $E                  # refs/REFS.md：定妆图、场景图、首帧的提示词（MJ 英文 / 即梦中文）
aigc-mv ep prompts $E               # units/<id>/：音频窗口、prompt.txt、request.json
aigc-mv ep approve $E --all         # 读过提示词再批准（花钱闸门）
# 在即梦生成，下载到 units/<id>/takes/take-1.mp4 …
aigc-mv ep sync $E u05              # 测量每条的口型延迟和跟丢位置
aigc-mv ep pick $E u05 take-2       # 人眼选条
aigc-mv ep render $E --test 0:15    # 先出一小段
aigc-mv ep render $E --res 1080p    # final/<标题>.mp4
```

没有素材的镜头会用首帧图按这个镜头的运镜做推拉摇移，连图也没有就放标注卡，所以花钱之前就能看到完整的动态分镜。

## 一期的文件夹

```
projects/<一期>/
  episode.yaml          唯一的创作源文件：演员、歌词（半句用空格分）、注释、动作、叙事插入、场景、画风
  audio/                song.wav  vocals.wav  instrumental.wav
  analysis/timing.json  节拍网格、每句 / 半句 / 每个字的时间、段落、每小节能量
  board/                board.json  board.md（分镜表）  audit.json
  refs/                 REFS.md + 你生成的 a_sheet.png  b_sheet.png  venue.png  loc_*.png  crowd.png  plate_u*.png
  units/<id>/           prompt.txt  request.json  <id>_vocal.wav  takes/  takes.json
  edit/                 edl.json  parts/  layers/
  final/                成片
  ledger.jsonl  approvals.json
```

示例产出（不用跑就能看）：[分镜表](docs/examples/项羽vs刘邦_分镜表.md) · [对口型提示词](docs/examples/项羽vs刘邦_u05_对口型提示词.txt) · [叙事插入提示词](docs/examples/项羽vs刘邦_u03_叙事插入提示词.txt) · [定妆图提示词](docs/examples/项羽vs刘邦_定妆图.md) · [Suno 栏](docs/examples/项羽vs刘邦_suno.md)

## episode.yaml 里最常改的字段

```yaml
grammar: hybrid        # show = 综艺擂台多机位 | mv = 叙事 MV | hybrid = 擂台用 show、叙事场景用 mv
look: night_arena      # night_arena | palace_day | battlefield_dusk | tv_arena（见 cinema.LOOKS）
verses:
  - who: a
    lines:
      - text: 巨鹿破釜沉舟 杀得秦军心慌     # 空格分前后半句
        note: 《史记·项羽本纪》：皆沉船，破釜甑……
        action: 空着的手往下狠狠一劈
        cutaway: 夜里河边，士兵砸破大锅、凿沉木船   # 后半句切到叙事插入
        location: julu
        camera: snap_zoom                        # 可选：强制运镜（cinema.MOVES）
        framing: CU                              # 可选：强制景别
```

## 模块

| 模块 | 作用 |
| --- | --- |
| `episode.py` | episode.yaml 的数据模型和校验（站位必须一左一右、场景要先定义） |
| `timing.py` | 节拍网格（相位搜索 + 每拍吸附到 ±30 ms 内的起音）、下拍、ASR / 网格两种对齐、段落 |
| `cinema.py` | 景别、镜头、运镜库、画风预设、真实感规则、禁用词 |
| `board.py` | 分镜规划、生成单元分组、审核、分镜表 |
| `prompts.py` | Seedance 剧本式提示词、定妆图 / 首帧提示词、Suno 栏 |
| `windows.py` | 每个单元的人声 / 伴奏窗口 |
| `sync.py` | 每条生成的延迟和同步区间测量 |
| `edit.py` / `overlays.py` | EDL、按帧对齐渲染、逐镜头调色、胶片感、字幕 / 注释 / 名字卡 / 标题 |
| `packs.py` | 写出每个单元的上传清单和请求 |
| `providers/` | 花钱闸门 + Dreamina / Suno 适配器（待接口，见 [docs/接口对接.md](docs/接口对接.md)） |

旧的知识层命令（`list-characters`、`get-canon`、`build-prompt`、`list-lore`、`lyric-brief`、`align`、`storyboard`、`preview`）保留不变，MCP 服务见 [`mcp_server/README.md`](mcp_server/README.md)。

## 红线

- 只做古人：不用近现代政治人物和在世真人，脸不要像任何演员。
- 典故层「借古讽今，不讽刺政治」的规则不变。
- 片头保留「AI生成 仅供娱乐」，发布时在平台勾选 AI 生成声明；Suno 免费版的歌不能商用；注释发布前对原文核一遍。

## 致谢与许可

MIT。方法和部分算法思路来自 [ancient-rap-battle](https://github.com/10291124jcjc-dotcom/ancient-rap-battle)（MIT，© 硅基废话）和 [claudia.gallery](https://claudia.gallery/) 公开的制作 wiki（anabology）；代码为重写，规则在文档里注明出处。字体在首次使用时从 Google Fonts 下载（SIL OFL）。
