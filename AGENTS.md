# Agent 操作规程：H3 出片

本文件写给代跑这条流水线的 agent（Claude Code、Codex、Kiro 等）。目标是同样的输入每次出同样的结果：
agent 只执行下面的命令，不替用户做创作或参数决定。细节见 [docs/H3_Colab.md](docs/H3_Colab.md)。

## 固定不变的部分（agent 不能改）

- **歌和口型**：Suno 整曲、逐角色干声、`analysis/timing.json`。口型由 H3 跟目标干声对齐，这条链路已验证，不改。
- **渲染配置** `model_profile`（在素材库 `defaults` 或本集 `h3_assets*.json` 里）：
  - `template_sha256`：唯一允许的 ComfyUI 工作流。换模板会被 `ep h3-bundle` 拒绝。
  - `steps`（可选）：固定步数。写了以后 `--steps` 只能省略或填同一个值。
  - `lora_strengths`（可选）：模板第 2、3 号 LoRA 节点的强度，默认 0。
- **素材**：角色肖像、首帧、场景图都从素材库按资产 ID 取，内容按 SHA256 校验。
- **导演计划** `direction.json`：每镜的机位、动作、持麦手，由导演填写并设为 `ready`。

要改上面任何一项，先停下来问用户。

## 每批镜头的固定步骤

```sh
E=projects/<本集>; A=$E/h3_assets.production.json; T=<已固定的工作流 JSON>
aigc-mv ep production-check $E --assets $A          # 不通过就停，把错误原样报给用户
aigc-mv ep h3-bundle $E --assets $A --template $T --out <新目录> --shots s001,s002
#   不传 --steps；输出里每镜的 job_id、seed、帧数原样记下
python <bundle>/run_h3.py --dry-run                   # 云端执行前先校验
python <bundle>/run_h3.py                             # 在 Colab G4 上跑，见 docs/H3_Colab.md
aigc-mv ep h3-ingest $E <bundle> <results>
```

## 验收、重抽和选条

1. 每条候选都要用 `ep h3-review` 写验收记录，五项（identity、performance、hands_props、lip_sync、continuity）
   都写观察到的证据。agent 可以起草，**`keep` 由用户确认**。
2. 需要重抽时，两种情况分开处理：
   - **只是随机性不好**（参数都对）：用下一个 take 号重新编译，`--take 2`、`--take 3`……
     同一个 take 号永远是同一个 seed，所以重跑 take 1 只会得到同一条。
   - **要改东西**：用 `ep h3-retake-plan` 写一项假设、一处改动，用户同意后再改配置并重新编译。
     一次只改一处，否则不知道是哪一处起的作用。
3. 一个镜头有多条通过时，用 `ep h3-select <ep> <shot> <job_id>` 选定。没选定时剪辑会报错，
   不会按文件顺序替你挑。

## 出成片

```sh
aigc-mv ep render $E --res 1080p --h3-only    # 有镜头没有通过的 H3 条就拒绝出片，并列出镜头号
```

## 禁止事项

- 不改 `seed_base`、`lead_frames`、`lock_guide_audio`、`model_profile`，不换模板，不传 `--steps`。
- 不为了省 CCU 降分辨率或减步数。
- 不在两次运行之间悄悄改 `direction.json`、`shot_overrides` 或提示词描述。
- 不把未通过验收或 pilot 的条放进成片。
- 提交结果不明的任务不重发，先查 ComfyUI 队列和历史（运行器也会拦）。
