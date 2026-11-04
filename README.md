# 《罗天大醮有嘻哈 第一期：诸葛青 VS 王也》交接包（handoff 分支）

这是《一人之下》同人二创的 AI 说唱综艺。图片、歌曲、分镜（board）和 44 个视频单元的提示词都已经做好，
**只差生成 44 段视频**。视频生成在原环境里被即梦账号的风控拦住了（见 `doc/dreamina_block.md`），
所以把素材打成这个包，由你在自己的电脑上、用本地 agent 接着做完：生成视频 → 导入 → 对口型测量与挑选 → 渲染 1080p 成片。

适合谁读：用户本人，以及本地的编程 agent（最后一节 “给本地 agent 的任务说明” 可以原样交给它）。

## 一、包里有什么

- `projects/wangye_vs_zhugeqing/`：集数项目文件，目录结构和代码仓库里的完全一样，直接复制合并即可。
  - `episode.yaml`、`analysis/timing.json`、`analysis/timing_report.md`
  - `board/board.json`（分镜）、`board/audit.json`、`board/board.md`
  - `units/<u01…u44>/`：`request.json`、`prompt.txt`、该单元的音频窗口 `.wav`；`units/summary.json`
  - `refs/`：定妆照 `<key>_face.png`、定妆组图 `<key>_sheet.png`（15 个人物）和 9 张场景图，全部是 AI 生成图，PNG 原样（无损）
  - `refs/candidates/picks.json`：当时的挑图记录
  - `audio_flac/`：整曲、主唱干声、伴奏三条 FLAC（切成 5 MB 一块的 `.partNN`），加 `whole_flac.sha256`
- `tools/restore_audio.py`：把 FLAC 分块合并并解码回流水线要的 `.wav`
- `doc/dreamina_block.md`：即梦风控拦截的说明
- `MANIFEST.md`（每个文件的用途和大小）、`SHA256SUMS`（校验）

## 二、不包含什么

- 官方《一人之下》原作图（`refs/canon/`）：有版权，不进仓库。生成图已经做完，视频阶段不需要它。
- 任何密钥、即梦登录状态、`ledger.jsonl`、`approvals.json`。
- 已渲染的视频（`final/`）、未选中的候选图、`.venv`。
- 单元里的参考图副本（`units/<id>/图片N_*.png`）：它们是从 `refs/` 缩放出来的，运行 `ep prompts` 会原样重新生成（见下）。
- 代码本身：在 GitHub 的代码分支里。

## 三、环境准备

需要 Python 3.11 或更高。

```bash
git clone -b feat/cinematic-battle-pipeline https://github.com/riversxiao/aigc-mv-pipeline.git
cd aigc-mv-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

`pyproject.toml` 的基础依赖（pydantic、typer、pyyaml、pillow、numpy、soundfile、imageio-ffmpeg）会自动装上。
ffmpeg 来自 imageio-ffmpeg 自带的静态版本，不用另外安装。
本流程不需要重新做歌词对齐，所以 `faster-whisper`、`pypinyin` 可以不装；
万一要重新跑 `ep analyze`，再执行 `pip install -e ".[asr]"`。

还需要即梦命令行 `dreamina-canvas`，并在你自己的电脑上登录（`dreamina-canvas auth login`）。

## 四、把资料包放进去

取得 handoff 分支（任选一种）：

```bash
git clone -b handoff https://github.com/riversxiao/aigc-mv-pipeline.git ../handoff
```

或者在 GitHub 上选 `handoff` 分支，Code → Download ZIP 解压。然后在代码仓库根目录执行（把路径换成实际位置）：

```bash
cp -R ../handoff/projects/wangye_vs_zhugeqing projects/      # 目录合并，保持相对路径不变
cp -R ../handoff/tools ./handoff_tools
```

目标位置必须是 `projects/wangye_vs_zhugeqing/`，流水线按这个相对路径找文件。

### 1. 还原音频（FLAC → WAV）

```bash
python handoff_tools/restore_audio.py projects/wangye_vs_zhugeqing
```

会先校验合并后 FLAC 的 sha256，再解码出 `audio/song.wav`、`audio/vocals.wav`、`audio/instrumental.wav`
（48 kHz、立体声、16 位，和原文件逐位一致，每个约 36 MB，时长 190.2 秒）。

手工做法（等价）：

```bash
cd projects/wangye_vs_zhugeqing/audio_flac
cat song.flac.part* > song.flac          # vocals、instrumental 同理
sha256sum -c whole_flac.sha256           # macOS 用 shasum -a 256 -c
ffmpeg -i song.flac -ar 48000 -ac 2 -c:a pcm_s16le ../audio/song.wav
```

### 2. 重新生成单元里的参考图

```bash
aigc-mv ep prompts projects/wangye_vs_zhugeqing
```

这一步会重写 `units/<id>/prompt.txt`、`request.json`、音频窗口，并生成 `units/<id>/图片N_*.png`。
文本和音频与包里的逐字节一致（已验证），所以不会改变任何提示词。

## 五、生成视频（解除风控之后）

先处理即梦账号的风控（`doc/dreamina_block.md`）。解除后：

```bash
aigc-mv ep dreamina-bundle projects/wangye_vs_zhugeqing --out ../dreamina_bundle
cd ../dreamina_bundle
python3 run_dreamina.py --units u01 --quote-only   # 先报价，不扣分
python3 run_dreamina.py --units u01                # 试跑 1 个单元，确认风控已解除
python3 run_dreamina.py                            # 跑全部 44 个单元（每个 1 条），可中断、可重跑
```

运行器会先报价、再提交，重跑不会重复扣分；详细说明在生成出来的 `dreamina_bundle/README.md`。
结果在 `dreamina_bundle/takes/<单元>/take-1.mp4`、`results.json` 和 `takes.zip`。
（运行器源码就是代码仓库里的 `src/aigc_mv/dreamina_runner.py`。）

## 六、导入、挑选、渲染 1080p

```bash
cd ../aigc-mv-pipeline        # 回到代码仓库，保持 .venv 已激活
aigc-mv ep ingest-takes projects/wangye_vs_zhugeqing ../dreamina_bundle   # 也可以给 takes.zip
aigc-mv ep status projects/wangye_vs_zhugeqing
aigc-mv ep render projects/wangye_vs_zhugeqing --res 1080p
```

`ingest-takes` 会把视频复制到 `units/<id>/takes/`，做口型对齐测量（`ep sync`）、自动挑选（`ep pick`），
并写出需要重拍的清单 `units/retakes.md`。不满意的单元可以单独重拍：
`python3 run_dreamina.py --units u05 --take 2`，再导入一次。
成片在 `projects/wangye_vs_zhugeqing/final/`。

## 七、给本地 agent 的任务说明

你是本地的编程 agent。请按顺序完成，每一步成功再做下一步，失败就停下来把原始报错报告给用户，不要改提示词和分镜。

1. 克隆代码：`git clone -b feat/cinematic-battle-pipeline https://github.com/riversxiao/aigc-mv-pipeline.git`，进入目录，
   `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`。
2. 取得 `handoff` 分支，把其中的 `projects/wangye_vs_zhugeqing/` 合并复制到代码仓库的 `projects/wangye_vs_zhugeqing/`，保持相对路径；
   把 `tools/restore_audio.py` 复制到代码仓库的 `handoff_tools/`。
3. 校验：在 handoff 目录里运行 `sha256sum -c SHA256SUMS`（macOS：`shasum -a 256 -c SHA256SUMS`），必须全部 OK。
4. 运行 `python handoff_tools/restore_audio.py projects/wangye_vs_zhugeqing`，确认 `audio/` 下有三个 36 MB 左右的 wav。
5. 运行 `aigc-mv ep prompts projects/wangye_vs_zhugeqing`，应显示 44 个单元、全部 `ok`；再运行 `aigc-mv ep status projects/wangye_vs_zhugeqing`。
6. 询问用户即梦账号的视频风控是否已经解除、`dreamina-canvas auth status` 是否显示 `"loggedIn":true`。没解除就停下，把 `doc/dreamina_block.md` 给用户看。
7. `aigc-mv ep dreamina-bundle projects/wangye_vs_zhugeqing --out ../dreamina_bundle`，进入该目录，
   先 `python3 run_dreamina.py --units u01 --quote-only`，把报价告诉用户，**得到用户同意后**再 `python3 run_dreamina.py --units u01`；
   成功后再 `python3 run_dreamina.py`（全部 44 个，要花积分，务必先让用户确认总报价）。电脑不要睡眠，中断后重跑同一条命令即可续跑。
8. 回到代码仓库：`aigc-mv ep ingest-takes projects/wangye_vs_zhugeqing ../dreamina_bundle`，读 `units/retakes.md`，把失败或口型对不上的单元列给用户；
   用户同意后用 `--units <ids> --take 2` 重拍并再次 ingest。
9. `aigc-mv ep render projects/wangye_vs_zhugeqing --res 1080p`，把 `projects/wangye_vs_zhugeqing/final/` 里的 mp4 路径告诉用户。
   遇到缺失单元时会用占位画面补，渲染输出里 `sources` 会统计每种来源的数量，请如实报告。

注意：不要把任何账号凭据、`.tools` 或即梦状态目录提交进 git；不要生成或上传 `refs/canon/` 里的官方原作图。
