# 罗天大醮的观众席：场景背景图

**是的，观众席要坐满人，背景图要做。** 即梦（Seedance 2.0 全能参考）是照着上传的图来认场馆的：如果只传一张空场馆，
或者干脆不传，生成出来的看台常常是空的、稀稀拉拉的，而且每条视频里的场馆都长得不一样，剪在一起就穿帮。参考片《火影有嘻哈03》
能像一档真节目，靠的也是满场的红黑场馆：开场高位全景、主持串场、反应切观众、片尾把话筒伸向观众，看台上一直是满的。

所以这一期给罗天大醮场馆的每个机位各做一张锁定的背景板（场景图），一共 9 张，每张做 4 张候选挑 1 张。
每个镜头按调度自动配一张（分镜表新加了「场景图」列），每个视频单元的【上传】里都有它，提示词里每个镜头写着「背景照 @图片N」。

按真歌（Drive 里那首 190.2 秒的成品）排出来的分镜，能看到满场观众的镜头主要是这些：

- 开场 0.00 到 1.71 秒的高位全景（s001，u01，`venue_high.png`）；
- 主歌里三次客串反应：风莎燕 61.73 秒（s022，u14），诸葛家长辈 65.17 秒和 93.95 秒（s024 / s035，u15 / u20），都用 `cameo_seats.png`；
- 收尾 154.91 秒王也把话筒伸向观众「你们站哪边」（s062，u34，`crowd_reverse.png`）；
- 「把声音给我」之后 Suno 多唱的那段女声啦啦啦（161 到 179 秒）和结尾：观众欢呼 s063 / s064 / s068（u35 / u36 / u40，`crowd.png`），高位全景 s065 / s069（u37 / u41，`venue_high.png`）。

揭晓前 138.90 到 146.42 秒的灭灯清唱（s055 到 s058，u29 到 u31）反过来：观众席是黑的，只有剪影和零星的荧光棒，用 `venue_dark.png`。

**没有生成任何图**，也没有调用任何付费接口；下面的费用只是估算，真要生成需要你先确认预算。
本页由 `aigc-mv ep refs` 生成的 refs/REFS.md「场景图 / 背景板」整理而来，`aigc-mv ep plates <本期目录>` 可以随时打印同样的清单和费用。

## 做哪些、不做哪些

| 场景图 | 用途 | 观众 | 用在镜头 | 用在单元（实际上传） |
| --- | --- | --- | --- | --- |
| `venue.png` | 主场景：选手、队友、对峙、双人镜头的背景（先做这张，锁定后其他场景图都参考它） | 坐满，看得清脸 | s005、s006、s007、s008、s010、s012、s013、s014 等 44 个 | u04、u05、u06、u07、u09、u11、u12、u13、u15、u16、u18、u19、u20、u21、u22、u23、u24、u25、u26、u27、u28、u33、u39、u43、u44 |
| `venue_high.png` | 开场和片尾的高位全景（摇臂镜头的起幅和落幅） | 坐满，看得清脸 | s001、s065、s069 | u01、u37、u41 |
| `venue_dark.png` | 揭晓前的灭灯：背影追光、空舞台、低头特写和追光特写的背景 | 灭灯，只有剪影 | s055、s056、s057、s058 | u29、u30、u31 |
| `crowd.png` | 观众欢呼的空镜（开场、间奏、片尾的观众镜头） | 坐满，看得清脸 | s063、s064、s068 | u35、u36、u40 |
| `crowd_reverse.png` | 反打：选手在台上把话筒伸向观众时，从台上往外看满场看台 | 坐满，看得清脸 | s062 | u34 |
| `cameo_seats.png` | 客串角色坐在观众席里的反应镜头（客串不画进这张图，座位留空） | 坐满，看得清脸 | s022、s024、s035 | u14、u15、u20 |
| `judges.png` | 评委反应镜头的背景 | 坐满，虚成光斑 | s020、s031、s044、s052 | u14、u18、u24、u27 |
| `dj_booth.png` | 主持和 DJ 镜头的背景 | 坐满，虚成光斑 | s002、s003、s004、s066、s070 | u02、u03、u38、u42 |
| `hook_mics.png` | 副歌歌手在立麦前唱的背景（舞台后方的两支立麦） | 坐满，虚成光斑 | s009、s011、s028、s059、s061 | u08、u10、u17、u32、u33 |

不单独做的：地面八卦图案和 LED 大屏的特写图（分镜里没有这两种插入镜头，它们已经在舞台正面、高位全景和 DJ 台三张里）；每位评委、每位客串各一张座位图（一张评委席、一张前两排座位就够，人物靠定妆图放进去）；白天、彩排、后台这类场景（这一期全在晚上的直播现场）。

## 怎么做

1. 先做 `venue.png`（文生图），每张出 2 到 4 张候选，挑一张锁定。锁定以后不再改，改了就要重新生成所有用到它的镜头。
2. 其他场景图都上传一张已经锁定的场景图当图1（每张下面的「上传」写了是哪张），这样灯光、配色、地面图案和看台样式能对上。Midjourney 里把那张锁定图当 `--sref <场景图链接>`；这是自己生成的图，不是官方图，传上去没问题。
3. 挑图标准：看台是满的，没有空座位；观众是长相各不相同的普通成年人，不是动漫脸、不像任何真实名人；画面里没有任何文字和标志（节目 logo 是剪辑时叠上去的角标）；和上一张锁定图放在一起像同一个场馆。

## 观众密度：图里坐满，提示词里再说一遍

两层都做：场景图本身就是满场（「看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样」），视频模型照着图生成时看台不会空；每个单元的提示词里还有一行【观众】，点名哪几个镜头能看到观众席，再写一次坐满、不要空座位、不要空看台。灭灯那几个镜头例外：观众席是黑的，只有剪影和零星的荧光棒，提示词也写明不要把观众照亮。

## 客串角色坐哪儿

客串角色不画进任何场景图。`cameo_seats.png` 把他们的座位留空：风莎燕坐在观众席第二排靠中间偏左；诸葛家长辈坐在观众席第一排正中。客串的反应镜头上传这个人的定妆组图和 `cameo_seats.png`，提示词写明坐在哪个座位（就是图里留空的那个），左右和身后是不认识的普通观众。同一个人的所有镜头用同一张图、同一句座位描述，所以位置不会跳。观众全景里不要求看到客串角色。

## 视频单元怎么上传

每个单元最多上传 9 张图（即梦 Seedance 2.0 全能参考的图片上限）：先放人物，每人只传一张定妆组图（最多 6 人），再放场景图，最多 2 张。一个单元里调度多于两种场景时，灭灯和客串座位这两张一定保留，其次保留画面里有那个人的专属场景图（评委反应配评委席、主持和 DJ 配 DJ 台、副歌歌手配立麦），其余按镜头时长选；超过上限时先去掉背景里虚化的队友，再去掉多出来的场景图。提示词的每个镜头都写了「背景照 @图片N」。

## 费用估算（没有生成任何图）

按 OpenRouter `openai/gpt-image-2.5-sunburst`、quality high、16:9 估算。账本里已经做过的 3:4 高质量图（带一张参考图）实际每张 $0.055 到 $0.060；16:9 是 1536x1024，和 3:4 的 1024x1536 像素一样多，所以按每张 $0.06 算，保守上限按每张 $0.12（2 倍，留给更长的提示词、多一张参考图或者调价）。每张场景图做 4 张候选。

| 场景图 | 候选张数 | 估算 USD | 保守上限 USD |
| --- | --- | --- | --- |
| `venue.png` | 4 | $0.24 | $0.48 |
| `venue_high.png` | 4 | $0.24 | $0.48 |
| `venue_dark.png` | 4 | $0.24 | $0.48 |
| `crowd.png` | 4 | $0.24 | $0.48 |
| `crowd_reverse.png` | 4 | $0.24 | $0.48 |
| `cameo_seats.png` | 4 | $0.24 | $0.48 |
| `judges.png` | 4 | $0.24 | $0.48 |
| `dj_booth.png` | 4 | $0.24 | $0.48 |
| `hook_mics.png` | 4 | $0.24 | $0.48 |
| 合计 | 36 | $2.16 | $4.32 |

付费生成要先确认预算再跑；这里只是估算，没有调用任何接口。

## `venue.png`
用途：主场景：选手、队友、对峙、双人镜头的背景（先做这张，锁定后其他场景图都参考它）

机位：全景，35mm 镜头，纪实感，人物和环境都看得清；从观众席正前方平视舞台，正面对称，地平线水平，台上没有人

用在镜头：s005、s006、s007、s008、s010、s012、s013、s014、s015、s016、s017、s018、s019、s021、s023、s025、s026、s027、s029、s030、s032、s033、s034、s036、s037、s038、s039、s040、s041、s042、s043、s045、s046、s047、s048、s049、s050、s051、s053、s054、s060、s067、s071、s072

用在单元：u04、u05、u06、u07、u09、u11、u12、u13、u15、u16、u18、u19、u20、u21、u22、u23、u24、u25、u26、u27、u28、u33、u39、u43、u44

上传：不上传图（文生图）

即梦 CN：
```
全景，35mm 镜头，纪实感，人物和环境都看得清，从观众席正前方平视舞台，正面对称，地平线水平，台上没有人，舞台在画面中间，背后是 LED 大屏和灯带，两侧和远处的看台层层叠叠，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样：18 到 60 岁的普通成年观众，男女都有，胖瘦、发型和便装各不相同，表情各异，不是动漫脸，不像任何真实名人，舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
wide shot, 35mm lens, documentary feel, straight-on symmetrical view of the stage from the audience at eye level, level horizon, nobody on stage, the stage centred with the LED wall and light strips behind it, tiered stands on both sides, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands
```
GPT Image（OpenRouter，参数已去掉）：
```
wide shot, 35mm lens, documentary feel, straight-on symmetrical view of the stage from the audience at eye level, level horizon, nobody on stage, the stage centred with the LED wall and light strips behind it, tiered stands on both sides, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands.
```

## `venue_high.png`
用途：开场和片尾的高位全景（摇臂镜头的起幅和落幅）

机位：全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视；从看台最高处往下拍的高位全景，看得到整个舞台、地面图案和四面看台，台上没有人

用在镜头：s001、s065、s069

用在单元：u01、u37、u41

上传：图1 = `refs/venue.png`（已锁定的场景图：保持同一个场馆、布景、灯光和配色）

即梦 CN：
```
图1是已经锁定的场景图 venue.png：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，从看台最高处往下拍的高位全景，看得到整个舞台、地面图案和四面看台，台上没有人，整个场馆一览无余，舞台灯光全亮，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样：18 到 60 岁的普通成年观众，男女都有，胖瘦、发型和便装各不相同，表情各异，不是动漫脸，不像任何真实名人，舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, high-angle wide shot from the top of the stands looking down at the whole stage, the floor graphic and the stands on every side, nobody on stage, the whole arena in one frame, all stage lights on, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --sref <场景图链接> --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands
```
GPT Image（OpenRouter，参数已去掉）：
```
The first input image is the locked plate of the same arena (venue.png): keep the same stage, floor graphic, LED wall, light strips, palette and seating, only the camera position changes. wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, high-angle wide shot from the top of the stands looking down at the whole stage, the floor graphic and the stands on every side, nobody on stage, the whole arena in one frame, all stage lights on, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands.
```

## `venue_dark.png`
用途：揭晓前的灭灯：背影追光、空舞台、低头特写和追光特写的背景

机位：全景，35mm 镜头，纪实感，人物和环境都看得清；和舞台正面那张同一个机位：正面平视，台上没有人

用在镜头：s055、s056、s057、s058

用在单元：u29、u30、u31

上传：图1 = `refs/venue.png`（已锁定的场景图：保持同一个场馆、布景、灯光和配色）

即梦 CN：
```
图1是已经锁定的场景图 venue.png：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位，全景，35mm 镜头，纪实感，人物和环境都看得清，和舞台正面那张同一个机位：正面平视，台上没有人，LED 大屏和灯带全部熄灭，只剩追光落在地面中央，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，观众席一片黑，只看得到前几排观众的黑色剪影和零星的红色荧光棒光点，全场灯灭，只有头顶一束冷白色追光直直打在舞台中央，追光里能看到薄烟，其余地方几乎全黑，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
wide shot, 35mm lens, documentary feel, the same straight-on eye-level camera as the main stage plate, nobody on stage, the LED wall and light strips switched off, only the spot on the centre of the floor, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, the audience is dark, only black silhouettes of the front rows and scattered red glow-stick dots, blackout, a single cold white follow spot straight down on the centre of the stage, haze visible in the beam, everything else near black, fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --sref <场景图链接> --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
GPT Image（OpenRouter，参数已去掉）：
```
The first input image is the locked plate of the same arena (venue.png): keep the same stage, floor graphic, LED wall, light strips, palette and seating, only the camera position changes. wide shot, 35mm lens, documentary feel, the same straight-on eye-level camera as the main stage plate, nobody on stage, the LED wall and light strips switched off, only the spot on the centre of the floor, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, the audience is dark, only black silhouettes of the front rows and scattered red glow-stick dots, blackout, a single cold white follow spot straight down on the centre of the stage, haze visible in the beam, everything else near black, fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark.
```

## `crowd.png`
用途：观众欢呼的空镜（开场、间奏、片尾的观众镜头）

机位：中景，腰以上，50mm 标准镜头；站在舞台边上平视前排看台，前三四排观众的脸看得清，后排层层叠叠

用在镜头：s063、s064、s068

用在单元：u35、u36、u40

上传：图1 = `refs/venue_high.png`（已锁定的场景图：保持同一个场馆、布景、灯光和配色）

即梦 CN：
```
图1是已经锁定的场景图 venue_high.png：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位，中景，腰以上，50mm 标准镜头，站在舞台边上平视前排看台，前三四排观众的脸看得清，后排层层叠叠，二三十个看得清脸的观众冲着舞台欢呼、举手，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样：18 到 60 岁的普通成年观众，男女都有，胖瘦、发型和便装各不相同，表情各异，不是动漫脸，不像任何真实名人，舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
medium shot, waist up, 50mm lens, from the stage edge at eye level toward the front sections, the first three or four rows clearly visible, more tiers rising behind, twenty to thirty clearly visible faces cheering toward the stage with raised hands, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --sref <场景图链接> --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands
```
GPT Image（OpenRouter，参数已去掉）：
```
The first input image is the locked plate of the same arena (venue_high.png): keep the same stage, floor graphic, LED wall, light strips, palette and seating, only the camera position changes. medium shot, waist up, 50mm lens, from the stage edge at eye level toward the front sections, the first three or four rows clearly visible, more tiers rising behind, twenty to thirty clearly visible faces cheering toward the stage with raised hands, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands.
```

## `crowd_reverse.png`
用途：反打：选手在台上把话筒伸向观众时，从台上往外看满场看台

机位：全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视；反打机位：从舞台后方越过舞台地面往外拍，前景是空的舞台边缘，看出去是满满的层层看台，台上没有人

用在镜头：s062

用在单元：u34

上传：图1 = `refs/venue_high.png`（已锁定的场景图：保持同一个场馆、布景、灯光和配色）

即梦 CN：
```
图1是已经锁定的场景图 venue_high.png：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，反打机位：从舞台后方越过舞台地面往外拍，前景是空的舞台边缘，看出去是满满的层层看台，台上没有人，观众朝台上挥手、张嘴喊，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样：18 到 60 岁的普通成年观众，男女都有，胖瘦、发型和便装各不相同，表情各异，不是动漫脸，不像任何真实名人，舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, reverse angle from the back of the stage across the empty stage floor, looking out at the packed tiered stands, nobody on stage, the audience waving and shouting toward the stage, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --sref <场景图链接> --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands
```
GPT Image（OpenRouter，参数已去掉）：
```
The first input image is the locked plate of the same arena (venue_high.png): keep the same stage, floor graphic, LED wall, light strips, palette and seating, only the camera position changes. wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, reverse angle from the back of the stage across the empty stage floor, looking out at the packed tiered stands, nobody on stage, the audience waving and shouting toward the stage, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands.
```

## `cameo_seats.png`
用途：客串角色坐在观众席里的反应镜头（客串不画进这张图，座位留空）

机位：中景，腰以上，50mm 标准镜头；坐着的眼睛高度平视观众席前两排，正对着看台，第一排和第二排都在画面里

用在镜头：s022、s024、s035

用在单元：u14、u15、u20

上传：图1 = `refs/venue_high.png`（已锁定的场景图：保持同一个场馆、布景、灯光和配色）

即梦 CN：
```
图1是已经锁定的场景图 venue_high.png：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位，中景，腰以上，50mm 标准镜头，坐着的眼睛高度平视观众席前两排，正对着看台，第一排和第二排都在画面里，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样：18 到 60 岁的普通成年观众，男女都有，胖瘦、发型和便装各不相同，表情各异，不是动漫脸，不像任何真实名人，观众席第二排靠中间偏左留一个空座位、观众席第一排正中留一个空座位（后面客串角色会坐进去），除此之外所有座位都坐满了人，舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
medium shot, waist up, 50mm lens, seated eye level facing the first two rows of the stands, both rows in frame, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, exactly one empty seat in the second row just left of centre and one empty seat in the front row centre left free for a later guest, every other seat taken, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --sref <场景图链接> --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands
```
GPT Image（OpenRouter，参数已去掉）：
```
The first input image is the locked plate of the same arena (venue_high.png): keep the same stage, floor graphic, LED wall, light strips, palette and seating, only the camera position changes. medium shot, waist up, 50mm lens, seated eye level facing the first two rows of the stands, both rows in frame, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, every tier packed with spectators, no empty seats, waving red glow sticks, ordinary adult audience aged 18 to 60, men and women with clearly different faces, builds, hairstyles and casual clothes, varied expressions, no anime faces, nobody resembling a real celebrity, exactly one empty seat in the second row just left of centre and one empty seat in the front row centre left free for a later guest, every other seat taken, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands.
```

## `judges.png`
用途：评委反应镜头的背景

机位：中景，腰以上，50mm 标准镜头；评委席的正面中景，座位上没有人

用在镜头：s020、s031、s044、s052

用在单元：u14、u18、u24、u27

上传：图1 = `refs/venue.png`（已锁定的场景图：保持同一个场馆、布景、灯光和配色）

即梦 CN：
```
图1是已经锁定的场景图 venue.png：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位，中景，腰以上，50mm 标准镜头，评委席的正面中景，座位上没有人，说唱节目的评委席：舞台边的高台上并排摆着三张高背深色木王座，红色轮廓光，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，背景里的看台也坐满了观众，虚成红色荧光棒的光斑，没有空座位，舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
medium shot, waist up, 50mm lens, medium shot of the judges' bench from the front, nobody seated, the judges' bench of a rap show: three tall dark wooden thrones side by side on a raised platform beside the stage, red rim light, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, the packed stands behind melted into bokeh of red glow sticks, no empty seats, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --sref <场景图链接> --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands
```
GPT Image（OpenRouter，参数已去掉）：
```
The first input image is the locked plate of the same arena (venue.png): keep the same stage, floor graphic, LED wall, light strips, palette and seating, only the camera position changes. medium shot, waist up, 50mm lens, medium shot of the judges' bench from the front, nobody seated, the judges' bench of a rap show: three tall dark wooden thrones side by side on a raised platform beside the stage, red rim light, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, the packed stands behind melted into bokeh of red glow sticks, no empty seats, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands.
```

## `dj_booth.png`
用途：主持和 DJ 镜头的背景

机位：中景，腰以上，50mm 标准镜头；DJ 台正面中景，台后没有人

用在镜头：s002、s003、s004、s066、s070

用在单元：u02、u03、u38、u42

上传：图1 = `refs/venue.png`（已锁定的场景图：保持同一个场馆、布景、灯光和配色）

即梦 CN：
```
图1是已经锁定的场景图 venue.png：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位，中景，腰以上，50mm 标准镜头，DJ 台正面中景，台后没有人，舞台后方的 DJ 台：黑色台子上两台唱机和一台调音台，几盏小台灯，背后是 LED 大屏，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，背景里的看台也坐满了观众，虚成红色荧光棒的光斑，没有空座位，舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
medium shot, waist up, 50mm lens, medium shot of the DJ booth from the front, nobody behind it, a DJ booth at the back of the stage: a black console with two turntables and a mixer, small lamps, the LED wall behind, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, the packed stands behind melted into bokeh of red glow sticks, no empty seats, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --sref <场景图链接> --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands
```
GPT Image（OpenRouter，参数已去掉）：
```
The first input image is the locked plate of the same arena (venue.png): keep the same stage, floor graphic, LED wall, light strips, palette and seating, only the camera position changes. medium shot, waist up, 50mm lens, medium shot of the DJ booth from the front, nobody behind it, a DJ booth at the back of the stage: a black console with two turntables and a mixer, small lamps, the LED wall behind, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, the packed stands behind melted into bokeh of red glow sticks, no empty seats, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands.
```

## `hook_mics.png`
用途：副歌歌手在立麦前唱的背景（舞台后方的两支立麦）

机位：中景，腰以上，50mm 标准镜头；立麦正面中景，没有人

用在镜头：s009、s011、s028、s059、s061

用在单元：u08、u10、u17、u32、u33

上传：图1 = `refs/venue.png`（已锁定的场景图：保持同一个场馆、布景、灯光和配色）

即梦 CN：
```
图1是已经锁定的场景图 venue.png：保持同一个场馆、同样的布景、灯光、配色和看台样式，只换成下面的机位，中景，腰以上，50mm 标准镜头，立麦正面中景，没有人，舞台后方并排两支银色立麦，话筒架是黑色的，背后是 LED 大屏，同一个场馆的同一套布景：罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影；LED 大屏上只有抽象的红色光纹，没有任何文字、标志和人像，地面图案上也没有字，背景里的看台也坐满了观众，虚成红色荧光棒的光斑，没有空座位，舞台顶部的硬光加两侧红色侧光，空气里有薄烟，像电视直播画面但有电影感，细腻颗粒，像电视直播现场拍下的真实照片，观众是真实的普通人，皮肤有真实纹理，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney EN：
```
medium shot, waist up, 50mm lens, medium shot of the standing microphones from the front, nobody there, two silver microphones on black stands side by side at the back of the stage, the LED wall behind, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, the packed stands behind melted into bokeh of red glow sticks, no empty seats, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --sref <场景图链接> --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands
```
GPT Image（OpenRouter，参数已去掉）：
```
The first input image is the locked plate of the same arena (venue.png): keep the same stage, floor graphic, LED wall, light strips, palette and seating, only the camera position changes. medium shot, waist up, 50mm lens, medium shot of the standing microphones from the front, nobody there, two silver microphones on black stands side by side at the back of the stage, the LED wall behind, the same arena set in every plate: a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back; the LED wall shows only abstract red light patterns, no text, no logo, no faces, the packed stands behind melted into bokeh of red glow sticks, no empty seats, hard top stage light with red side light, thin haze, broadcast realism with cinematic fine grain, a real photograph taken during a live TV broadcast, real ordinary people with natural skin texture, no text, no letters, no logos. Landscape 16:9. Avoid: cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark, empty seats, empty stands.
```
