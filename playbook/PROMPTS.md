# H3 / 视频提示词骨架

少堆形容词，多写**可执行**的动作与连续。

```
Emotion: <一句情绪>
Action: <单一主动作，起势→收势>
Camera: <景别 + 运镜 + 大致焦段感>
Continuity: <与首尾帧一致的服装/手/机位说明>
Lighting: <主光方向 + 色温；呼应 Venue Bible cue>
Nobody speaks: <非口型镜写上>
No subtitles / no watermark / no extra limbs
```

## 禁用（人物主镜）

- ref2va（脸易漂）  
- 空洞词堆：`8K, masterpiece, cinematic, best quality` 代替动作  

## 饱满感（伪 3D 写实）

参考拉片结论：观感「饱满」多来自 **体积光 + 浅景深 + 定妆锁脸 + fl2va**，不是先建一套完整 Blender 角色。提示词写清 rim light / volumetric / shallow DOF，仍走首尾帧纪律。
