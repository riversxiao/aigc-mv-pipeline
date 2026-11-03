# 即梦（Dreamina）视频生成包

视频在 **用户自己已经登录即梦的电脑** 上生成：流水线这边把每个单元的提示词、参考图、音频片段和一个运行脚本打成一个包，
用户解压后一条命令跑完 44 个单元，再把 `takes.zip` 发回来。脚本只用 Python 3 标准库，macOS 自带的 `python3` 即可。

每个单元只生成 **1 条**（take-1）。以前每段 2 条是为了“抽卡”：同样的提示词每次结果不同，多生成几条挑最好的。
现在先每段 1 条看整体，哪几段不满意再只重拍那几段，积分花在刀刃上。

## 一、命令

```bash
# 流水线这边：生成包（默认写到 <本期>/dreamina_bundle，并在小于 95 MB 时另写 dreamina_bundle.zip）
aigc-mv ep dreamina-bundle projects/wangye_vs_zhugeqing --out /path/dreamina_bundle

# 只打包几个单元、生成第 2 条（重拍）
aigc-mv ep dreamina-bundle projects/wangye_vs_zhugeqing --units u05,u09 --take 2 --out /path/retake_2

# 用户电脑上：
cd dreamina_bundle && python3 run_dreamina.py              # 全部单元
python3 run_dreamina.py --quote-only                       # 只上传、建节点、报价，不扣分
DREAMINA_CREDIT_CAP=3000 python3 run_dreamina.py           # 本次最多花 3000 积分（或 --credit-cap 3000）
python3 run_dreamina.py --units u05 --take 2               # 重拍某个单元
python3 run_dreamina.py --dry-run                          # 演练：只打印写操作
DREAMINA_CANVAS=/完整路径/dreamina-canvas python3 run_dreamina.py   # 命令行不在 PATH 里时
```

其他参数：`--parallel`（同时生成几个，默认 3）、`--interval`（查询间隔秒，默认 15）、`--max-wait`（每个单元本次最多等几分钟，默认 60）、
`--model`（指定模型）、`--project-id`（指定画布）。

## 二、包里有什么

| 路径 | 内容 |
| --- | --- |
| `run_dreamina.py` | 运行脚本，就是仓库里的 `src/aigc_mv/dreamina_runner.py` 原样复制 |
| `README.md` | 给用户的中文说明（准备、一键命令、积分、重跑、发回方式、单元清单） |
| `manifest.json` | 本期名称、take 号、单元列表、每个文件大小、脚本校验值 |
| `images/` | 本期用到的定妆组图和场景图，每张只放一份（只有生成图，`refs/canon/` 官方原图一律不打包，打包时按文件内容校验） |
| `units/<单元>/request.json` | 提示词、图片顺序（图片1、图片2…）、音频、时长、分辨率、画幅；路径都相对包的根目录 |
| `units/<单元>/prompt.txt` | 同一份提示词，方便阅读或在网页端手动用 |
| `units/<单元>/<单元>_vocal.wav` 或 `_inst.wav` | 这个单元的歌曲片段（唱段是人声，无口型段是伴奏） |

运行后会多出：`state.json`（断点续跑记录）、`logs/<单元>.log` 和 `logs/<单元>.prompt.txt`（实际发出的提示词）、
`takes/<单元>/take-N.mp4`、`results.json`、`takes.zip`。

## 三、脚本做了什么

1. **检查**：`dreamina-canvas version`、`auth status`（没登录就提示 `dreamina-canvas auth login` 后退出）、`auth account`（会员、可用积分）。
2. **选模型**（每次运行实时查询）：`model find seedance --type video` 和 `model list --type video`，在 Seedance 模型里选：
   多模态参考（`m2v`）且图片和音频能同时参考的优先，其次版本更高、pro 优于标准优于 fast/lite、参考槽位更多。
   读出这个模式的参考上限（图片、音频、合计）、互斥类型、可选时长、分辨率、画幅，再用 `model <模型> --type video` 看是不是样片模型和素材限制。全部写进日志。
3. **按模型规定调整每个单元**：
   - 时长：单元时长本身可选就用它，否则用 **不短于** 它的最近一档（剪辑时裁掉多余部分）；
   - 分辨率 720P（不可选时用最接近的），画幅 16:9；
   - 参考数超过上限：先去掉场景图，再去掉后面的人，唱段的主唱（图片1）和音频始终保留；
   - 模型不能同时参考图片和音频：唱段改用首帧模式（没有音频参考，口型要人工检查；`ep sync` 只有在成片原样带着这段音频时才能量对齐），
     无口型段保留图片、不传音频（成片音轨以原曲为准）。
   - 提示词里的 `@图片N`、`@音频1` 换成即梦命令行的引用占位符 `{{res:<素材ID>}}`，这样每个名字都绑定到对应素材；被去掉的图在提示词里改用人名。
4. **画布和素材**：新建（或复用）一个画布；每个文件按内容只上传一次。
5. **先报价**：每个单元保存一个视频节点（不生成）并 `node quote`，汇总打印总报价。
6. **积分闸门**：总报价超过上限（`DREAMINA_CREDIT_CAP` / `--credit-cap`，默认总报价 + 10%）或超过账号可用积分，就一分不花直接停。
   每个节点用 **它自己的报价** 作为 `node confirm --credit-ceiling`，拿到的确认凭证只在内存里交给 `node run --credit-token`，不写文件、不进日志。
   价格变高（确认失败）就停下这个单元，标成“需要重新确认积分”。
7. **提交和等待**：提交前先把提交 ID 写进 `state.json`，再 `node run --submit-id`；之后只用 `operation wait <提交ID> --project-id <画布> --timeout 0`
   轮询（只读）。同时最多 3 个在生成，生成完一个补一个。
8. **下载**：`resource download <素材ID> -o takes/<单元>/take-N.mp4`，检查文件大小和 mp4 文件头。命令行下不了时（见第五节），
   把画布链接和素材 ID 打出来，请用户在网页上下载。
9. **收尾**：`results.json`（每个单元的状态、文件、校验值、模型、模式、时长、报价、调整说明、节点 ID、提交 ID、素材 ID）和 `takes.zip`。

## 四、断点续跑和不重复扣分

- 画布 ID 由本期名称确定，素材 ID 由画布和文件内容确定，节点 ID、更新 ID、提交 ID 由画布、单元和 take 号确定，都是固定的。
  即使 `state.json` 丢了，重跑也会落到同一个画布、同一个节点、同一个提交 ID 上。
- 已提交（或提交结果不确定）的单元 **永远不会换新的提交 ID 重新提交**，重跑只会继续 `operation wait`。
  只有服务端明确说“这次提交不存在且可以重提”时，才用 **同一个** 提交 ID 再提交一次；查不到又不能重提的，标成“需要人工确认”。
- 等待超时（默认 60 分钟）只是本次先放下，下次运行接着等。
- 重拍用新的 take 号（`--take 2`），这是唯一会产生新提交 ID、再次扣分的方式。

## 五、下载方式和 7 天期限

即梦命令行 v1.2.1 的 `resource download` 在说明里写的是“下载成功的图片素材”，`resource get` 明确不返回任何链接，
所以视频能不能用命令行下载要到真实账号上才知道。脚本先试 `resource download`；不行就把画布链接和每条视频的素材 ID 打出来，
请用户在网页画布上找到标题为 `u05 take-1` 这样的节点下载，按 `takes/u05/take-1.mp4` 放好，再跑一次脚本重新打包。

即梦的视频样片最多保存 7 天，过期后不能再用来生成正式视频，所以生成完要尽快下载、发回。

## 六、发回、导入、重拍

1. 用户把 `takes.zip` 上传到 Google Drive，共享设为“知道链接的任何人可查看”，把链接发回来。
2. 导入：下载 `takes.zip`（或解压后的文件夹、整个 `dreamina_bundle` 文件夹都行，外面多套一层文件夹也能认），然后一条命令：

   ```bash
   .venv/bin/aigc-mv ep ingest-takes projects/wangye_vs_zhugeqing ~/Downloads/takes.zip
   ```

   它依次做四件事：
   - 复制：`takes/<单元>/take-N.mp4` 放进 `units/<单元>/takes/`。已有一模一样的文件就跳过；同名但内容不同的另存为
     `take-N.v2.mp4`，不会覆盖原文件。不认识的单元、不是 mp4 的文件（比如网页登录页）跳过并提示。
     `results.json` 里每条成片的模型、模式、状态、说明记到 `units/ingest.json`。
   - 量口型：对每个导入了成片的单元跑一遍 `ep sync`（唱段：成片音轨和参考音频对齐，得出 lag、ncc、是否复刻、对上的时间段；
     动作段或没有音轨的成片：只记时长）。
   - 自动挑选：每个单元选最好的一条（唱段：口型对上的优先，再看时长够不够、ncc 高、lag 小；动作段：时长够的里面最长的）。
     你用 `ep pick <本期> <单元> <take>` 手动选过的不会被改，除非加 `--force`。
   - 重拍清单：写 `units/retakes.json` 和 `units/retakes.md`，列出没有成片、口型没对上、成片比单元短、生成失败或审核未通过的单元，
     并给出现成的重拍命令；首尾帧模式（`first_last_frame`）的唱段单独列为“口型靠肉眼检查”，不自动算重拍；
     状态是 `manual_download` 的单元提示去网页画布手动下载后再导入一次。

   单独重跑某一步：

   ```bash
   .venv/bin/aigc-mv ep sync projects/wangye_vs_zhugeqing u05      # 重新量一个单元
   .venv/bin/aigc-mv ep pick projects/wangye_vs_zhugeqing --auto    # 重新自动挑选（--force 连手动选的也改）
   .venv/bin/aigc-mv ep pick projects/wangye_vs_zhugeqing u05 take-2 --notes "表情更好"   # 手动指定
   .venv/bin/aigc-mv ep retakes projects/wangye_vs_zhugeqing        # 重新生成重拍清单
   ```

3. 出片：

   ```bash
   .venv/bin/aigc-mv ep render projects/wangye_vs_zhugeqing --res 1080p
   ```

   有成片的镜头用挑中的成片（按量出的 lag 对齐歌曲），没有的用占位画面，输出 `final/<标题>.mp4`，1920x1080。
   成片尺寸或帧率不一样也没关系：宽高比接近 16:9 的放大裁满，差得多的（方形、竖屏）等比缩放加黑边，帧率统一成本期帧率。
   先看一小段可以加 `--test 0:15`。

4. 重拍：把清单里的命令复制出来跑，例如

   ```bash
   .venv/bin/aigc-mv ep dreamina-bundle projects/wangye_vs_zhugeqing --units u05,u09 --take 2
   ```

   打一个小包发给用户，用户照样 `python3 run_dreamina.py`，同一期的重拍包会落到同一个画布上。
   拿回来的 `takes.zip` 再 `ep ingest-takes` 一次即可，take-2 和 take-1 一起参与自动挑选。

## 七、已知风险

- 模型能力（参考上限、可选时长、分辨率）只能在登录后实时查询，沙盒里没有登录，没法预先验证；脚本每次运行都会重新查询并记日志。
- 视频下载可能需要在网页上手动完成（见第五节）。
- 报价单位是即梦积分，具体数额只有登录后报价才知道；用户可以先 `--quote-only` 看总数。
- 提示词带引用占位符后会变长；如果超过模型的提示词长度上限，脚本改用 `@图片N` 文字（按上传顺序对应），仍然超长就跳过这个单元并报错，不会自动截断。
- 内容审核可能拒绝个别单元，脚本会列出并给出重拍命令。
