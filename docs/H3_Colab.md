# Colab H3 镜头适配

本分支 `codex/h3-mv-adapter` 在原歌曲、时间轴和剪辑器之上增加 H3 镜头任务。
原始 handoff 素材保留；新版美术通过独立资产表指定，不覆盖原图。

## 系列共享资产与第二期

共享库位于 `libraries/luotian/catalog.json`。资产使用稳定角色 ID，例如
`asset:character.wang_ye.front.v1`，不把 `a` / `b` 舞台位置当作角色身份。
同一角色换到左右另一侧时，肖像仍能引用正确人物；多人合成首帧还会核对参与角色和固定左右站位。

| 资产 | 跨集复用条件 |
| --- | --- |
| 单角色正面、背面、服装与道具参考 | 同一角色与造型版本；单张纯净参考分别保存 |
| 空舞台与黑场环境 | 同一舞台与灯光状态 |
| 双人、团队和观众合成首帧 | 参与人物与固定站位均匹配；不匹配时制作新首帧 |
| 声线参考 | 角色音色试听通过后共享；当前库尚无已定样声线 |
| 歌曲、逐角色干声和时间轴 | 每期重新制作；不能直接复用上期唱词 |

`objects/` 存放按内容哈希命名的只读图片，新增版本使用新资产 ID。Git 只保存目录索引和配置，
图片字节需随素材包一并备份。新库已经整理了 15 个角色、16 张人物参考（含王也背身）、15 张合成首帧、2 张空场环境。

第二期先准备自己的 `episode.yaml`，再创建共享配置：

```sh
aigc-mv ep shared-assets projects/ep02 --library libraries/luotian/catalog.json
# 自动按 cast.<位置>.character 绑定肖像；新一集的 keyframes 与声线试听记录仍待填写。
aigc-mv ep production-check projects/ep02 --assets projects/ep02/h3_assets.json
```

该检查只读本地文件，不分配 GPU。它核对图片哈希、角色、站位、背身参考、歌词时间轴，
以及真实的人声素材与试听记录。`schema_version: 3` 及以上的正式 H3 导出会强制执行检查。
新建配置默认使用 `schema_version: 4`，还要求完整的导演计划和其中声明需要的骨骼素材；
已有 schema 3 配置和历史任务仍按原规则兼容，显式配置导演计划后也会检查该计划。
历史配置需要显式 `--allow-legacy-audio` 才能重新编译；已有历史任务包可以按原校验值续跑。
该兼容选项保留旧音频，不代表角色声线已经合格，不应用于新集绕过检查。

### 角色声线

配置的 `audio_cast.voices` 以真实角色 ID 为键。每名有台词或唱词的角色提供独立 `voice_id`、
声音参考 `reference`、本期独立人声 `vocals`。独立人声按整首歌时间轴保存，在其他角色的段落留静音。
H3 的可见演唱镜头从对应角色干声提取 guide，成片使用已经确认的整曲混音。

```json
{
  "voice_id": "wang_ye_v1",
  "reference": "asset:voice.wang_ye.v1",
  "vocals": "audio/wang_ye_vocals.wav"
}
```

声音参考可通过 `ep asset-register --library ... --id voice.wang_ye.v1 --source ... --kind voice --characters wang_ye`
登记。试听同一句歌词的角色 A/B 样声，并核对实际整曲混音后，再记录结果：

```sh
aigc-mv ep voice-review projects/ep02 --assets projects/ep02/h3_assets.json
aigc-mv ep voice-review projects/ep02 --assets projects/ep02/h3_assets.json \
  --approve --notes '已比较角色音色与实际混音，逐字时序已核对'
```

相同的声音参考或干声不能用不同名字重复绑定给不同角色；静音占位轨也会被拦截。
混音、伴奏、角色干声、声音参考、歌词或角色分配变化后，试听记录会失效，需要重新听检。
这是文件绑定与人工听检记录校验，不能自动证明两个真实声音足够不同。

### 逐镜参考与备份

背身镜头可在 `shot_overrides.<镜头>.portraits` 中单独绑定背身参考，其他镜头继续使用正面参考。
单人背身首帧会检查参考角度，并使用背身表演描述，避免混入正脸眼神表演指令。
新格式的任务 ID 同时计入实际工作流、音频锁定实现、模型配置和声线试听版本，减少错误复用旧结果。

```sh
aigc-mv ep asset-pack --library libraries/luotian/catalog.json --out luotian-assets-v1.zip
aigc-mv ep asset-unpack luotian-assets-v1.zip --out libraries/luotian_restored
```

恢复会校验每项资产的 SHA256，并拒绝覆盖已有目录。素材包不包含凭据、模型权重或本期歌曲。
`projects/wangye_vs_zhugeqing/h3_assets.shared.json` 是第一期图片映射的迁移示例：图片检查通过，
声线仍标记待定，不能把第一期原曲音色问题当作已经解决。

## 导演计划、骨骼库和逐镜验收

方法来源与 H3 适配边界见 [吸收记录](UPSTREAM_Seedance.md)。
骨骼素材库由独立流程建设，交接要求见 [素材库接口](Motion_Library_Handoff.md)。

```sh
aigc-mv ep direct-plan projects/ep02 --assets projects/ep02/h3_assets.json
aigc-mv ep direction-check projects/ep02 --assets projects/ep02/h3_assets.json
```

`direct-plan` 根据实际分镜和可见角色生成草稿，并将路径写入资产配置。
在 `direction.json` 里补齐舞台轴线与地标、机位、灯光、人物位置/朝向/视线、
一个主要动作、情绪、准备/重音/收势、画面内的结束姿态、其他人的自然反应、持麦手和位置。
字段完成后将逐镜 `status` 设为 `ready`。需要身体动作参考的镜头还要绑定素材库中的稳定版本 ID。
程序检查结构与匹配关系，导演仍要判断动作是否好看、收势是否自然。

计划会直接编译到 H3 提示词，替代泛化的点头与随机比划；不只是一份旁路文档。
引用职责固定为：角色图控制身份与服装，首帧控制舞台、构图与光线，骨骼参考控制身体动作，
镜头计划控制摄影，目标干声控制演唱时钟。动作参考原声不会进入图或替换角色声音。
计划、镜头调度或动作素材变化会产生新的任务身份；库所在机器的绝对路径不参与该身份。

索引没到或角色声线没定样时，预检会如实列出未完成项，不能启动正式导出。
不需要重做所有骨骼片段来匹配同一固定秒数；编译时按每镜实际窗口在本地适配动作视频。

新任务导入后带五项待验收记录：`identity`、`performance`、`hands_props`、`lip_sync`、`continuity`。
无可见演唱的镜头不要求 `lip_sync`。所有适用项都写明观察证据并通过，才能以 `keep` 进入剪辑。
试验镜头的 pilot 标记仍会阻止其直接进入正式剪辑。

```json
{
  "job_id": "实际任务ID",
  "video_sha256": "实际视频SHA256",
  "verdict": "retake",
  "checks": {
    "identity": {"status":"pass", "evidence":"全段人物与批准定妆一致"},
    "performance": {"status":"pass", "evidence":"1.0秒重音压手，话尾收势"},
    "hands_props": {"status":"fail", "evidence":"1.2秒话筒遮住嘴唇"},
    "lip_sync": {"status":"pass", "evidence":"逐字听看并核对起止与停顿"},
    "continuity": {"status":"pass", "evidence":"持麦手、服装、站位与舞台灯光稳定"}
  }
}
```

上面是填写结构示例，不是任何已有成片的审核结果。

```sh
aigc-mv ep h3-review projects/ep02 s001 实际任务ID --review review.json
aigc-mv ep h3-retake-plan projects/ep02 s001 实际任务ID --proposal change.json --out retake.json
```

`change.json` 包含一个 `hypothesis` 和仅一个 `changes` 条目，例如
`{"field":"direction.shots.s001.microphone.position","value":"lower sternum"}`。
输出保留父任务、视频哈希、失败证据和原参数，状态仅为提案，不改原片、不提交重拍。
改好实际配置后重新编译，再审阅新结果；提交不明或已有 latent 的原任务仍不得盲目重发。

## 动作参考试验

2026-11-06，用户观看王也三版同句样片后，明确选择骨骼参考版，评价为“明显更好”。
后续需要明确手势的单人演唱镜头优先采用骨骼视频参考；制作策略见
`libraries/luotian/motion_policy.json`。每镜仍需选取符合角色性格的动作，匹配持麦手、景别、
歌词重拍和收势停顿。这项偏好不替代新镜头的人物、手部和口型验收，也不会自动启动批量生成。

`aigc_mv.h3_motion.compile_comparison` 将一个独立单人 pilot 任务扩展为三版：
同一角色、首帧、目标人声、随机种子和采样参数，分别使用文字动作、原视频参考和骨骼视频参考。
参考视频需预处理成与任务等帧数的 24 fps 无声视频；编译会实际解码校验，并把视频哈希纳入任务身份。
原视频的音轨不连接到 H3，所有版本仍由本集目标人声驱动。

```python
from pathlib import Path
from aigc_mv.h3_motion import compile_comparison

compile_comparison(Path('baseline_bundle'), Path('raw_reference.mp4'),
                   Path('pose_reference.mp4'), Path('comparison'),
                   'Free hand makes two small accents, then returns to a held pose.')
```

安装可选工具使用 `pip install -e '.[motion]'`。该模块只编译本地任务，不申请 GPU；
云端仍需现有运行器、结果持久化校验与有界自动释放流程。

当前接法是 `LoadVideo → GetVideoComponents.images → MiniMaxH3ReferenceToVideo.ref_videos`。
骨骼视频在这里是视觉参考，不是逐帧 Pose/Depth ControlNet；也不是绑定骨骼的三维白模。
三种方式的效果需要实测，不能因接入参考就宣称动作已经精确跟随。
试验输出保留 pilot 标记，不能自动替换正式镜头。此项试验也不代表角色声线问题已修复。

## 最小试跑

先用 s013（诸葛青）和 s033（王也）两句已有干声验证音频引导。每条 90 帧，24 fps，3.75 秒；
开头保留音频引导余量，歌词原速不变。测试临时简化为单人固定近景，原分镜保持不变。
测试镜头带 `pilot_override` 标记，即使口型满意也不会自动替换正片的完整调度。

使用本任务的启动器：

```sh
./outputs/h3-mv-pilot/aigc-mv ep h3-bundle \
  outputs/aigc-mv-pipeline/projects/wangye_vs_zhugeqing \
  --assets outputs/h3-mv-pilot/assets.json \
  --template outputs/colab-ultra-workstation/workflows/01_dialogue_2p_photorealistic/workflow_v9_final.json \
  --out outputs/h3-mv-pilot/new-bundle --shots s013,s033
```

编译只在本机执行。目标目录已存在会报错，缺少指定定妆照、首帧或音频会在上传前报错。

```sh
python outputs/h3-mv-pilot/new-bundle/run_h3.py --dry-run
```

云端运行器连接当前 VM 的本地 ComfyUI，先校验素材，再按镜头提交。
目标音频进入 `MiniMaxH3AddGuide.audio` 并从第 0 帧锚定，角色肖像进入 `ref_images`；
原对白流程的音色参考不承担目标歌词的定时驱动。
每条结果保存原始视频、AV latent、实际工作流历史和输入校验值。
提交结果不明时不会自动重复提交，须先核对 Comfy 队列和历史。

## 导入与验收

```sh
./outputs/h3-mv-pilot/aigc-mv ep h3-ingest \
  outputs/aigc-mv-pipeline/projects/wangye_vs_zhugeqing \
  outputs/h3-mv-pilot/bundle outputs/h3-mv-pilot/results
```

候选进入 `projects/wangye_vs_zhugeqing/h3/shot_takes.json`，默认状态为 `unreviewed`。
音轨相关性不能证明画面嘴型准确。需要分别检查音节起止、停顿闭口、人物身份、手与话筒、服装和舞台连续性。
只有 `visual_status` 与 `identity_status` 都为 `pass`、没有测试调度标记且文件校验值一致的正式镜头，
才会被原剪辑器优先选入 EDL。修改过分镜时间或素材文件的记录会报错。

正式制作使用独立的 `assets_v2.json`：15 个角色、23 类首帧构图，绑定原分镜的 72 个镜头。
`mode=production` 保留各镜头的景别、镜头运动和表演；不沿用试跑的固定近景覆盖。
黑场和背身镜头可逐镜指定 `look_description`、`gallery_description`、`acting_description`，
替换通用的面部布光与正脸表演提示，避免它们和黑场/背向机位冲突。背身人物使用独立的纯净背身参考。
跨切镜不接上一镜的 AV latent；真正连续镜头可另建连续任务。
最终混音始终使用原 48 kHz 整曲，字幕与节目包装在本地合成。

## 音频与断点

`MiniMaxH3AddGuide.audio` 是软引导，不能单凭接入它就认定生成歌声与原曲逐句一致。
启用 `audio_lock` 时，`H3LockGuideAudio` 将引导音频编码为 audio latent，音频噪声掩码置零，
视频掩码保持一；采样只更新视频。云端必须同时安装随包提供的 `h3_audio_lock.py` 节点。
验收分别检查生成音轨与 guide 的时序、可见嘴型、停顿闭口；最终仍舍弃生成音轨，使用原曲。

采样后的 AV latent 必须先经 `H3SaveAVLatent`，再进入视频/音频解码。
只把保存节点并联为另一个输出，执行顺序可能落在解码之后，解码失败时就没有断点。
运行器发现已有原生 latent 会要求恢复解码，不能重新 POST 同一镜头浪费采样；
提交结果不明的任务也不能自动重发。

## 逐镜验收与成片

原剪辑器可兼容旧素材；本次全片交付由 `work/mv_conform_h3.py` 加严约束：
72 镜全部有正式 H3 候选、视觉与身份均通过、候选 ID 与 `final_selection.json` 一致，
且所有 EDL 来源为 `h3/takes/`。任何缺镜都会中止，不会混入旧 Seedance 或静帧。
`work/mv_verify_final.py` 再核对整片可解码、帧数、1080p/24 fps、48 kHz 原曲时序和逐镜来源。
Drive 最终交付还须核对文件大小与 MD5，并记录实际返回的视频链接。

## 算力

本地编译、图像生成、音频切分和 Drive 上传先完成。GPU 只负责模型加载与视频推理。
使用 96 GB G4。长任务以 `nohup` 脱离本机连接运行，同时让真实 Jupyter 内核任务监视
渲染 PID、状态文件和采样进度；单靠读取 Drive 文件不代表内核仍在执行任务。
内核监视只在实际生产任务存活时运行，完成或失败就退出。
本地通过 IOPub 接收该任务的真实输出；连接中断时刷新会话信息并重新订阅同一内核，
不会再次提交监视代码或视频任务。仅看到内核 `busy` 不能证明本机仍连接着它。
监视同时保存小型 RAM/显存快照和 ComfyUI 日志尾部，以便云端意外结束后排查。

批次执行器在完成或失败时，经 Drive API 校验已完成 MP4 与原生 latent 的大小、MD5，
写入并校验 `cloud_release.json` 后释放本次会话；另有有界 watchdog 兜底。
本地下载还需逐文件 SHA256 校验。结束后查账号实时速率与活跃会话，确认均为零。
云端意外结束且没有释放回执时，记录实际已保存镜头和未知结束时间，不能用后来检查时间
冒充 GPU 运行终点。各批次的 `ccu_usage.json` 区分余额差值与运行时间估算，余额可能延迟结算。
图像、字幕、剪辑和 Drive 交付在本地完成，期间不保持空闲 GPU。
