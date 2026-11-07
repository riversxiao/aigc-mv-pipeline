# 《异人开麦 / 一人之下》全系列总素材库 Pipeline 接入指南

本文档说明跨会话构建的 **《异人开麦》全系列总素材库（Master Asset Library）** 如何原生接入 `aigc-mv-pipeline` 的视觉资产解析器（`aigc_mv.shared_assets.AssetLibrary`）、多品类动作解析器（`aigc_mv.motion_assets.MotionLibrary`）、导演镜头规划器（`aigc_mv.directing`）与 CLI 工具链（`aigc-mv ep`）。

---

## 1. 视觉与角色资产命名空间（`AssetLibrary`）

`src/aigc_mv/shared_assets.py` 中的 `AssetLibrary` 除支持原有的内容寻址引用 `asset:<id>` 外，新增支持以下 6 类统一命名空间（均支持 SHA-256 完整性校验与 Google Drive 云端文件 ID 映射）：

| 命名空间前缀 | 对应索引文件 / 目录 | 示例用法 | 用途说明 |
| :--- | :--- | :--- | :--- |
| `asset:<id>` | `libraries/luotian/catalog.json` (`objects/`) | `asset:character.wang_ye.front.v1` | 已审核 3D 角色正/背立绘、首帧构图、场景与角色音色样本 |
| `charsheet:<id>` | `libraries/luotian/character_sheets/character_sheets_catalog.json` | `charsheet:feng_baobao`<br>`charsheet:quadview.zhang_zhiwei_young.v1` | 90+ 张 16:9 3D 四视图全身设定图（含童年/少年/青年/成年多时期角色变体） |
| `wardrobe:<id>` | `libraries/luotian/character_sheets/character_sheets_catalog.json` | `wardrobe:xia_he`<br>`wardrobe:wardrobe4x.feng_baobao.v1` | 女性核心角色 16:9 四套高定舞台穿搭设定图（冯宝宝、夏禾、陆玲珑、风莎燕、枳瑾花等） |
| `stage_v2:<id>` | `libraries/luotian/stage_v2/catalog.json` | `stage_v2:master_panorama`<br>`stage_v2:rivals_thunder_duel` | Stage v2.0 龙虎天枢·万象雷坛 16:9 殿堂级舞台全景与多机位舞美首帧 |
| `meoogo:<id>` | `libraries/luotian/meoogo_refs/meoogo_characters_catalog.json` | `meoogo:丁嶋安`<br>`meoogo:C002300935903` | 全宇宙 378 名角色原著/设定集 2D 基准图鉴 |
| `meoogo_16x9:<id>` | `libraries/luotian/meoogo_padded_16x9/` | `meoogo_16x9:赵方旭`<br>`meoogo_16x9:丁嶋安` | 全宇宙 378 名角色 1344×768 16:9 H3 标准构图输入垫图 |
| `timeline:<label>` | `libraries/luotian/meoogo_refs/meoogo_timeline_multi_age_catalog.json` | `timeline:TL_1944_timeEvent_234_冯宝宝苏醒` | 46 张甲申之乱至现代时间线/多年龄段原著参考卡 |

### 自动角色绑定与多时期变体支持
- **自动回退绑定（`scaffold_shared_assets`）**：新分集在执行 `aigc-mv ep shared-init` 时，若 `episode.yaml` 中的角色不在首期 22 人基础库中，`AssetLibrary.character_profile()` 会自动检索 `character_sheets_catalog.json` 与 `meoogo_characters_catalog.json`，绑定对应的 `charsheet:<id>` 或 `meoogo_16x9:<id>`。
- **多时期变体（`age_variant`）**：支持 `library.character_profile("wang_ye", age_variant="child")` 或在镜头 `shot_overrides.<shot_id>.portraits` 中指定 `charsheet:quadview.wang_ye_child.v1`、`charsheet:quadview.zhang_zhiwei_young.v1`，并通过 `production_readiness()` 校验。
- **Google Drive 云端映射（`cloud_info`）**：通过 `library.cloud_info(reference)` 直接查询 `libraries/luotian/master_asset_library_drive.json` 中已同步的 1,080+ 个云端文件 `file_id` 与链接。

---

## 2. 联邦式多品类动作与 3D 白模库（`MotionLibrary`）

`src/aigc_mv/motion_assets.py` 中的 `MotionLibrary` 支持传入单个 `catalog.json` 或动作总目录 `libraries/motions`，自动聚合并跨目录解析以下全部动作子库：

1. **`battle_rap`** (`libraries/motions/battle_rap/catalog.json`)：说唱舞台单人 2D 133 关键点全身+手部骨骼与 3D 雕塑白模。
2. **`luotian_combat`** (`libraries/motions/luotian_combat/catalog.json`)：115 条高燃武术打斗动作参考，含：
   - 52 条单人 3D 关节人体白模（`3d_whitemodel_mannequin`, `.white.v1`）
   - 52 条单人 2D 全身+手部骨骼（`2d_wholebody_skeleton_rtmw`, `.skel.v2`）
   - 11 条双人对战 3D 白模（`3d_whitemodel_duel_mannequin`, `.duel_white.v1`, `people: 2`）
3. **`instruments`** (`libraries/motions/instruments/catalog.json`)：钢琴（郎朗/Peter Bence/Animenz）、电吉他/指弹吉他（Polyphia/Ichika Nito）、三味线/古琴等 3D 白模+乐器代理与 21 关节手部特写。
4. **`kpop_dance`** (`libraries/motions/kpop_dance/catalog.json`)：K-pop 男团/女团（Jung Kook、j-hope、Jennie 等）8K 直拍提炼的 3D 白模与 2D 骨骼舞蹈模板。
5. **`piano` / `drums` / `stage_performance`**：舞台器乐与架子鼓专向动作包。

### 导演规划器（`directing.py`）动作绑定扩展
在分集 `direction.json` 的 `shots.<shot_id>.motion` 中支持：
- **跨品类直接引用**：即使 `h3_assets.json` 的 `motion_library` 指向 `libraries/motions/battle_rap/catalog.json`，也可直接引用 `instruments.*`、`kpop_dance.*`、`luotian_combat.*`。
- **双人对战白模（`people: 2`）**：双人交手镜头可配置 `{"asset_id": "luotian_combat.yin_yang_thunder_duel.s053_140_08.duel_white.v1", "people": 2, "allow_free_hands": true}`。
- **器乐/舞蹈/武术解放双手（`allow_free_hands: true`）**：非持麦镜头或仅参考躯干动态的镜头可绑定 `microphone_hand: "none"` 的器乐/武术/舞蹈动作。

---

## 3. CLI 巡检与检索命令

```bash
# 查看全系列视觉/角色设定图库与多品类动作库总览统计
aigc-mv ep asset-library-summary

# 按品类、姿态格式（3D白模/2D骨骼）、人数、景别或角色检索动作资产
aigc-mv ep motion-search --category luotian_combat --people 2
aigc-mv ep motion-search --category kpop_dance --pose-format rigged_3d_white_mannequin
aigc-mv ep motion-search --category instruments --tag piano
```
