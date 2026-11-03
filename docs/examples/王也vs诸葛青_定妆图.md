# 定妆图与场景图 · 诸葛青vs王也

## 为什么分三步

以前一句文生图直接出「四宫格定妆照」：四格里的脸常常不是同一个人，发色和标志物也会跑偏。现在改成三步，每一步都拿上一步锁定的图当参考：

1. **原作图 → 真人正面像**（`<key>_face.png`）：推荐把官方图直接从本地上传给即梦图片生成（图1）。也可以在 Midjourney 里当图片提示（链接放最前面，`--iw 1.5`，只借颜色和构图，不借画风），但要先看下面关于链接的说明。原创角色没有原作图，直接文生图。
2. **用正面像生成其他角度**：四分之三侧面、正侧面、半身、全身，每张单独生成，每张都上传第一步锁定的`<key>_face.png`（即梦图1；Midjourney V7 用 `--oref <定妆正面像链接> --ow 100`，V6 用 `--cref <定妆正面像链接> --cw 100`）。表情四宫格（`<key>_expr.png`）是可选的：只用来试表情、挑招牌表情，不拼进组图，视频单元也不用它，赶时间可以跳过。
3. **锁定并拼图**：face/34/profile/half/full 五张都挑好后跑 `aigc-mv ep sheets <本期目录>`，拼成 `<key>_sheet.png`（左边全身，右边 2x2 四张，接近 3:2，传给视频模型时脸不会被缩得太小）。五张没齐不会拼；想先拼着看加 `--partial`，这样拼出来的图 `ep prompts` 会继续提示缺图。视频单元每人只传这一张；锁定后不再改，改了就要重新生成所有用到这个人的镜头。

原作图只放在本地 `refs/canon/`（`aigc-mv ep canon` 放进去），这个文件夹在 .gitignore 里，官方图有版权，不进 git，也不要自己公开发布。

关于 Midjourney 链接：Midjourney 只认图片链接，在 Midjourney 网页里上传的图会存到它的服务器上，拿到的链接别人也能打开，等于把图放到了网上；隐身模式（Stealth）只是不进公开图库，链接本身照样能打开。所以第一步的原作图请用即梦本地上传，`<原作图链接>` 那条 Midjourney 提示词只在你接受这张官方图留在 Midjourney 服务器上时再用。第二步上传的是自己生成的真人正面像，不是官方图，上传后复制链接替换提示词里的 `<定妆正面像链接>` 即可。

挑图标准：每张生成 4 张挑 1 张。发色、发型、眼睛颜色和招牌物件要对得上原作；脸是原创的，不像任何真人演员，尤其不像真人剧《异人之下》的演员，也不照搬任何已有 AI 节目里的脸；皮肤有真实纹理、不塑料；成年人比例；第二步的五张必须一眼看出是第一步那个人。即梦用 CN，Midjourney 用 EN，EN 末尾的参数已经写好，不要再加画质堆砌词。

## 上传清单

| 人物 | 第一步上传 | 第二步上传 | 第三步 |
| --- | --- | --- | --- |
| 诸葛青（a） | `refs/canon/zhuge_qing.jpg` | `a_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `a_sheet.png` |
| 王也（b） | `refs/canon/wang_ye.jpg` | `b_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `b_sheet.png` |
| 诸葛白（zhuge_bai） | `refs/canon/zhuge_bai.jpg` | `zhuge_bai_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `zhuge_bai_sheet.png` |
| 诸葛家门人（menren） | 无（原创角色，文生图） | `menren_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `menren_sheet.png` |
| 张楚岚（chulan） | `refs/canon/zhang_chulan.jpg` | `chulan_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `chulan_sheet.png` |
| 武当师弟（daotong） | 无（原创角色，文生图） | `daotong_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `daotong_sheet.png` |
| 张之维（tianshi） | `refs/canon/zhang_zhiwei.jpg` | `tianshi_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `tianshi_sheet.png` |
| 陆瑾（lu_jin） | `refs/canon/lu_jin.jpg` | `lu_jin_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `lu_jin_sheet.png` |
| 风正豪（feng_zhenghao） | `refs/canon/feng_zhenghao.jpg` | `feng_zhenghao_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `feng_zhenghao_sheet.png` |
| 徐四（xu_si） | `refs/canon/xu_si.jpg` | `xu_si_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `xu_si_sheet.png` |
| 徐三（xu_san） | `refs/canon/xu_san.jpg` | `xu_san_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `xu_san_sheet.png` |
| 冯宝宝（baobao） | `refs/canon/feng_baobao.jpg` | `baobao_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `baobao_sheet.png` |
| 张灵玉（lingyu） | `refs/canon/zhang_lingyu.jpg` | `lingyu_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `lingyu_sheet.png` |
| 风莎燕（shayan） | `refs/canon/feng_shayan.jpg` | `shayan_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `shayan_sheet.png` |
| 诸葛家长辈（zhanglao） | 无（原创角色，文生图） | `zhanglao_face.png`（4 张必做 + 1 张可选，各传一次） | `ep sheets` 拼 `zhanglao_sheet.png` |

## 诸葛青（a）

原作图：`refs/canon/zhuge_qing.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/61836)）

原作里的样子：官方图：深藏青色（偏蓝的黑）头发，长侧刘海盖住一边额头，后面头发到后颈；眼睛一直眯成两道弯线，嘴角带笑；白色敞领衬衫，最上面两颗扣子不扣，深棕色细背带，外面敞穿一件深炭灰西装外套；脖子上一根细绳挂着绿色玉坠；嘴里什么都没有。

### 第一步 原作图 → 真人正面像

#### `a_face.png`
用途：诸葛青（选手）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/zhuge_qing.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，招牌特征不能丢：深藏青色长侧刘海 + 一直眯着笑的眼睛 + 细绳上的绿色玉坠，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, signature details that must stay: dark navy-blue hair with a long side fringe, eyes always narrowed into smiling curves, a green jade pendant on a thin cord, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `a_34.png`
用途：诸葛青（选手）第二步 四分之三侧面：上传锁定的 a_face.png 生成

上传：图1 = `refs/a_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛青的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸朝右，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，招牌特征不能丢：深藏青色长侧刘海 + 一直眯着笑的眼睛 + 细绳上的绿色玉坠，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned to the right, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, signature details that must stay: dark navy-blue hair with a long side fringe, eyes always narrowed into smiling curves, a green jade pendant on a thin cord, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `a_profile.png`
用途：诸葛青（选手）第二步 正侧面：上传锁定的 a_face.png 生成

上传：图1 = `refs/a_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛青的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸朝右，看得清侧脸轮廓和发型，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，招牌特征不能丢：深藏青色长侧刘海 + 一直眯着笑的眼睛 + 细绳上的绿色玉坠，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing to the right, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, signature details that must stay: dark navy-blue hair with a long side fringe, eyes always narrowed into smiling curves, a green jade pendant on a thin cord, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `a_half.png`
用途：诸葛青（选手）第二步 半身：上传锁定的 a_face.png 生成

上传：图1 = `refs/a_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛青的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微朝右，穿全套舞台服装，右手拿着银色有线话筒，话筒在嘴的斜下方，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，招牌特征不能丢：深藏青色长侧刘海 + 一直眯着笑的眼睛 + 细绳上的绿色玉坠，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly to the right in the full stage wardrobe, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, signature details that must stay: dark navy-blue hair with a long side fringe, eyes always narrowed into smiling curves, a green jade pendant on a thin cord, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `a_expr.png`
用途：诸葛青（选手）第二步 表情四宫格：上传锁定的 a_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/a_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛青的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（眯着眼笑，脑袋轻轻歪着，手指在话筒上一下一下敲拍子），四格都是正面头肩，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，招牌特征不能丢：深藏青色长侧刘海 + 一直眯着笑的眼睛 + 细绳上的绿色玉坠，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, signature details that must stay: dark navy-blue hair with a long side fringe, eyes always narrowed into smiling curves, a green jade pendant on a thin cord, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `a_full.png`
用途：诸葛青（选手）第二步 全身：上传锁定的 a_face.png 生成

上传：图1 = `refs/a_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛青的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体朝右，穿全套舞台服装和鞋，右手拿着银色有线话筒，话筒在嘴的斜下方，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，招牌特征不能丢：深藏青色长侧刘海 + 一直眯着笑的眼睛 + 细绳上的绿色玉坠，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned to the right, full stage costume and shoes, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, signature details that must stay: dark navy-blue hair with a long side fringe, eyes always narrowed into smiling curves, a green jade pendant on a thin cord, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `a_sheet.png`
用途：诸葛青（选手）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含诸葛青的生成都上传，只认脸，不当画面）

拼图用：`a_face.png`、`a_34.png`、`a_profile.png`、`a_half.png`、`a_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 王也（b）

原作图：`refs/canon/wang_ye.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/61837)）

原作里的样子：官方图：黑发在头顶后方挽成一个圆发髻，几缕长碎发从额前垂下来贴着脸；眼皮半耷拉着，眼神懒散放松，嘴角似笑非笑；穿深藏青色宽松的交领外套（道袍式领口），布料垂坠。

### 第一步 原作图 → 真人正面像

#### `b_face.png`
用途：王也（选手）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/wang_ye.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，25 岁的中国男人，高个，肩膀松垮微驼；长脸，鼻梁直，眼皮半耷拉着、眼神懒散；黑发在头顶后方挽成圆发髻，几缕长碎发垂在脸边；胡子刮净，上镜淡妆，皮肤有毛孔，眼下有倦色，招牌特征不能丢：头顶的黑色圆发髻加垂在脸边的碎发 + 半耷拉着的懒散眼睛 + 深藏青色交领外套，宽大的深藏青色交领工装外套松松披着，白色素T恤，深藏青色打褶阔腿裤，黑色高帮帆布鞋，深色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 25-year-old Chinese man, tall with relaxed slightly slouched shoulders, a long face with a straight nose, lazy half-lidded dark eyes and low relaxed eyebrows, black hair pulled up into a round topknot at the back of the crown with several long loose strands falling over the forehead and framing the face, clean-shaven, light on-camera stage makeup, real skin with fine pores and faint tired shadows under the eyes, signature details that must stay: black hair in a round topknot with loose strands framing the face, lazy half-lidded eyes, a dark navy crossed-collar jacket, an oversized dark navy work jacket cut with a Taoist crossed collar, worn loose and slightly off the shoulders over a plain white T-shirt, loose dark navy pleated wide trousers, black canvas high-top shoes, a dark wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `b_34.png`
用途：王也（选手）第二步 四分之三侧面：上传锁定的 b_face.png 生成

上传：图1 = `refs/b_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是王也的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸朝左，25 岁的中国男人，高个，肩膀松垮微驼；长脸，鼻梁直，眼皮半耷拉着、眼神懒散；黑发在头顶后方挽成圆发髻，几缕长碎发垂在脸边；胡子刮净，上镜淡妆，皮肤有毛孔，眼下有倦色，招牌特征不能丢：头顶的黑色圆发髻加垂在脸边的碎发 + 半耷拉着的懒散眼睛 + 深藏青色交领外套，宽大的深藏青色交领工装外套松松披着，白色素T恤，深藏青色打褶阔腿裤，黑色高帮帆布鞋，深色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 25-year-old Chinese man, tall with relaxed slightly slouched shoulders, a long face with a straight nose, lazy half-lidded dark eyes and low relaxed eyebrows, black hair pulled up into a round topknot at the back of the crown with several long loose strands falling over the forehead and framing the face, clean-shaven, light on-camera stage makeup, real skin with fine pores and faint tired shadows under the eyes, signature details that must stay: black hair in a round topknot with loose strands framing the face, lazy half-lidded eyes, a dark navy crossed-collar jacket, an oversized dark navy work jacket cut with a Taoist crossed collar, worn loose and slightly off the shoulders over a plain white T-shirt, loose dark navy pleated wide trousers, black canvas high-top shoes, a dark wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `b_profile.png`
用途：王也（选手）第二步 正侧面：上传锁定的 b_face.png 生成

上传：图1 = `refs/b_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是王也的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸朝左，看得清侧脸轮廓和发型，25 岁的中国男人，高个，肩膀松垮微驼；长脸，鼻梁直，眼皮半耷拉着、眼神懒散；黑发在头顶后方挽成圆发髻，几缕长碎发垂在脸边；胡子刮净，上镜淡妆，皮肤有毛孔，眼下有倦色，招牌特征不能丢：头顶的黑色圆发髻加垂在脸边的碎发 + 半耷拉着的懒散眼睛 + 深藏青色交领外套，宽大的深藏青色交领工装外套松松披着，白色素T恤，深藏青色打褶阔腿裤，黑色高帮帆布鞋，深色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 25-year-old Chinese man, tall with relaxed slightly slouched shoulders, a long face with a straight nose, lazy half-lidded dark eyes and low relaxed eyebrows, black hair pulled up into a round topknot at the back of the crown with several long loose strands falling over the forehead and framing the face, clean-shaven, light on-camera stage makeup, real skin with fine pores and faint tired shadows under the eyes, signature details that must stay: black hair in a round topknot with loose strands framing the face, lazy half-lidded eyes, a dark navy crossed-collar jacket, an oversized dark navy work jacket cut with a Taoist crossed collar, worn loose and slightly off the shoulders over a plain white T-shirt, loose dark navy pleated wide trousers, black canvas high-top shoes, a dark wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `b_half.png`
用途：王也（选手）第二步 半身：上传锁定的 b_face.png 生成

上传：图1 = `refs/b_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是王也的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微朝左，穿全套舞台服装，右手拿着银色有线话筒，话筒在嘴的斜下方，25 岁的中国男人，高个，肩膀松垮微驼；长脸，鼻梁直，眼皮半耷拉着、眼神懒散；黑发在头顶后方挽成圆发髻，几缕长碎发垂在脸边；胡子刮净，上镜淡妆，皮肤有毛孔，眼下有倦色，招牌特征不能丢：头顶的黑色圆发髻加垂在脸边的碎发 + 半耷拉着的懒散眼睛 + 深藏青色交领外套，宽大的深藏青色交领工装外套松松披着，白色素T恤，深藏青色打褶阔腿裤，黑色高帮帆布鞋，深色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly to the left in the full stage wardrobe, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 25-year-old Chinese man, tall with relaxed slightly slouched shoulders, a long face with a straight nose, lazy half-lidded dark eyes and low relaxed eyebrows, black hair pulled up into a round topknot at the back of the crown with several long loose strands falling over the forehead and framing the face, clean-shaven, light on-camera stage makeup, real skin with fine pores and faint tired shadows under the eyes, signature details that must stay: black hair in a round topknot with loose strands framing the face, lazy half-lidded eyes, a dark navy crossed-collar jacket, an oversized dark navy work jacket cut with a Taoist crossed collar, worn loose and slightly off the shoulders over a plain white T-shirt, loose dark navy pleated wide trousers, black canvas high-top shoes, a dark wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `b_expr.png`
用途：王也（选手）第二步 表情四宫格：上传锁定的 b_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/b_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是王也的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（半耷拉着眼皮听，打了个小哈欠，嘴角却慢慢挑起来），四格都是正面头肩，25 岁的中国男人，高个，肩膀松垮微驼；长脸，鼻梁直，眼皮半耷拉着、眼神懒散；黑发在头顶后方挽成圆发髻，几缕长碎发垂在脸边；胡子刮净，上镜淡妆，皮肤有毛孔，眼下有倦色，招牌特征不能丢：头顶的黑色圆发髻加垂在脸边的碎发 + 半耷拉着的懒散眼睛 + 深藏青色交领外套，宽大的深藏青色交领工装外套松松披着，白色素T恤，深藏青色打褶阔腿裤，黑色高帮帆布鞋，深色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 25-year-old Chinese man, tall with relaxed slightly slouched shoulders, a long face with a straight nose, lazy half-lidded dark eyes and low relaxed eyebrows, black hair pulled up into a round topknot at the back of the crown with several long loose strands falling over the forehead and framing the face, clean-shaven, light on-camera stage makeup, real skin with fine pores and faint tired shadows under the eyes, signature details that must stay: black hair in a round topknot with loose strands framing the face, lazy half-lidded eyes, a dark navy crossed-collar jacket, an oversized dark navy work jacket cut with a Taoist crossed collar, worn loose and slightly off the shoulders over a plain white T-shirt, loose dark navy pleated wide trousers, black canvas high-top shoes, a dark wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `b_full.png`
用途：王也（选手）第二步 全身：上传锁定的 b_face.png 生成

上传：图1 = `refs/b_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是王也的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体朝左，穿全套舞台服装和鞋，右手拿着银色有线话筒，话筒在嘴的斜下方，25 岁的中国男人，高个，肩膀松垮微驼；长脸，鼻梁直，眼皮半耷拉着、眼神懒散；黑发在头顶后方挽成圆发髻，几缕长碎发垂在脸边；胡子刮净，上镜淡妆，皮肤有毛孔，眼下有倦色，招牌特征不能丢：头顶的黑色圆发髻加垂在脸边的碎发 + 半耷拉着的懒散眼睛 + 深藏青色交领外套，宽大的深藏青色交领工装外套松松披着，白色素T恤，深藏青色打褶阔腿裤，黑色高帮帆布鞋，深色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned to the left, full stage costume and shoes, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 25-year-old Chinese man, tall with relaxed slightly slouched shoulders, a long face with a straight nose, lazy half-lidded dark eyes and low relaxed eyebrows, black hair pulled up into a round topknot at the back of the crown with several long loose strands falling over the forehead and framing the face, clean-shaven, light on-camera stage makeup, real skin with fine pores and faint tired shadows under the eyes, signature details that must stay: black hair in a round topknot with loose strands framing the face, lazy half-lidded eyes, a dark navy crossed-collar jacket, an oversized dark navy work jacket cut with a Taoist crossed collar, worn loose and slightly off the shoulders over a plain white T-shirt, loose dark navy pleated wide trousers, black canvas high-top shoes, a dark wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `b_sheet.png`
用途：王也（选手）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含王也的生成都上传，只认脸，不当画面）

拼图用：`b_face.png`、`b_34.png`、`b_profile.png`、`b_half.png`、`b_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 诸葛白（zhuge_bai）

原作图：`refs/canon/zhuge_bai.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/127662)）

原作里的样子：官方图：亮蓝色齐下巴的波波头，大而圆的蓝眼睛，张嘴大笑；头戴浅灰色礼帽，帽带是深酒红色；白色高立领衬衫，袖子挽到小臂，深灰色背带，黑裤子；一只手伸出来比剪刀手。和哥哥一样是白衬衫配背带。

### 第一步 原作图 → 真人正面像

#### `zhuge_bai_face.png`
用途：诸葛白（队友）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/zhuge_bai.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，20 岁的成年中国男人，中等个子偏瘦，圆脸；眼睛又大又圆、亮而急切，深蓝灰色虹膜，咧嘴笑；亮蓝色齐下巴波波头；上镜淡妆，皮肤有毛孔，鼻梁上几颗淡雀斑，招牌特征不能丢：亮蓝色波波头 + 浅灰色礼帽（深酒红帽带）+ 白衬衫配灰背带，浅灰色礼帽配深酒红帽带，白色高立领衬衫挽袖，深灰色背带，黑色收脚裤，白球鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 20-year-old adult Chinese man, of average height and lean, a round face with full cheeks, big round bright eyes with dark blue-grey irises, an open eager grin, bright blue chin-length bob hair with a soft fringe, light on-camera stage makeup, real skin with fine pores and a few faint freckles on the nose, signature details that must stay: a bright blue chin-length bob, a light grey fedora with a dark wine band, a white shirt with grey suspenders, a light grey fedora with a dark wine band, a white shirt with a tall open collar and sleeves rolled to the forearm, dark grey suspenders with silver clips, black tapered trousers, white leather sneakers, the same shirt-and-suspenders family look as Zhuge Qing, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `zhuge_bai_34.png`
用途：诸葛白（队友）第二步 四分之三侧面：上传锁定的 zhuge_bai_face.png 生成

上传：图1 = `refs/zhuge_bai_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛白的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸朝右，20 岁的成年中国男人，中等个子偏瘦，圆脸；眼睛又大又圆、亮而急切，深蓝灰色虹膜，咧嘴笑；亮蓝色齐下巴波波头；上镜淡妆，皮肤有毛孔，鼻梁上几颗淡雀斑，招牌特征不能丢：亮蓝色波波头 + 浅灰色礼帽（深酒红帽带）+ 白衬衫配灰背带，浅灰色礼帽配深酒红帽带，白色高立领衬衫挽袖，深灰色背带，黑色收脚裤，白球鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned to the right, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, of average height and lean, a round face with full cheeks, big round bright eyes with dark blue-grey irises, an open eager grin, bright blue chin-length bob hair with a soft fringe, light on-camera stage makeup, real skin with fine pores and a few faint freckles on the nose, signature details that must stay: a bright blue chin-length bob, a light grey fedora with a dark wine band, a white shirt with grey suspenders, a light grey fedora with a dark wine band, a white shirt with a tall open collar and sleeves rolled to the forearm, dark grey suspenders with silver clips, black tapered trousers, white leather sneakers, the same shirt-and-suspenders family look as Zhuge Qing, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `zhuge_bai_profile.png`
用途：诸葛白（队友）第二步 正侧面：上传锁定的 zhuge_bai_face.png 生成

上传：图1 = `refs/zhuge_bai_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛白的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸朝右，看得清侧脸轮廓和发型，20 岁的成年中国男人，中等个子偏瘦，圆脸；眼睛又大又圆、亮而急切，深蓝灰色虹膜，咧嘴笑；亮蓝色齐下巴波波头；上镜淡妆，皮肤有毛孔，鼻梁上几颗淡雀斑，招牌特征不能丢：亮蓝色波波头 + 浅灰色礼帽（深酒红帽带）+ 白衬衫配灰背带，浅灰色礼帽配深酒红帽带，白色高立领衬衫挽袖，深灰色背带，黑色收脚裤，白球鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing to the right, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, of average height and lean, a round face with full cheeks, big round bright eyes with dark blue-grey irises, an open eager grin, bright blue chin-length bob hair with a soft fringe, light on-camera stage makeup, real skin with fine pores and a few faint freckles on the nose, signature details that must stay: a bright blue chin-length bob, a light grey fedora with a dark wine band, a white shirt with grey suspenders, a light grey fedora with a dark wine band, a white shirt with a tall open collar and sleeves rolled to the forearm, dark grey suspenders with silver clips, black tapered trousers, white leather sneakers, the same shirt-and-suspenders family look as Zhuge Qing, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `zhuge_bai_half.png`
用途：诸葛白（队友）第二步 半身：上传锁定的 zhuge_bai_face.png 生成

上传：图1 = `refs/zhuge_bai_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛白的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微朝右，穿全套舞台服装，20 岁的成年中国男人，中等个子偏瘦，圆脸；眼睛又大又圆、亮而急切，深蓝灰色虹膜，咧嘴笑；亮蓝色齐下巴波波头；上镜淡妆，皮肤有毛孔，鼻梁上几颗淡雀斑，招牌特征不能丢：亮蓝色波波头 + 浅灰色礼帽（深酒红帽带）+ 白衬衫配灰背带，浅灰色礼帽配深酒红帽带，白色高立领衬衫挽袖，深灰色背带，黑色收脚裤，白球鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly to the right in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, of average height and lean, a round face with full cheeks, big round bright eyes with dark blue-grey irises, an open eager grin, bright blue chin-length bob hair with a soft fringe, light on-camera stage makeup, real skin with fine pores and a few faint freckles on the nose, signature details that must stay: a bright blue chin-length bob, a light grey fedora with a dark wine band, a white shirt with grey suspenders, a light grey fedora with a dark wine band, a white shirt with a tall open collar and sleeves rolled to the forearm, dark grey suspenders with silver clips, black tapered trousers, white leather sneakers, the same shirt-and-suspenders family look as Zhuge Qing, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `zhuge_bai_expr.png`
用途：诸葛白（队友）第二步 表情四宫格：上传锁定的 zhuge_bai_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/zhuge_bai_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛白的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（站在诸葛青身后压低礼帽偷看对面，一脸崇拜地跟着节奏点头，偷偷比了个剪刀手），四格都是正面头肩，20 岁的成年中国男人，中等个子偏瘦，圆脸；眼睛又大又圆、亮而急切，深蓝灰色虹膜，咧嘴笑；亮蓝色齐下巴波波头；上镜淡妆，皮肤有毛孔，鼻梁上几颗淡雀斑，招牌特征不能丢：亮蓝色波波头 + 浅灰色礼帽（深酒红帽带）+ 白衬衫配灰背带，浅灰色礼帽配深酒红帽带，白色高立领衬衫挽袖，深灰色背带，黑色收脚裤，白球鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, of average height and lean, a round face with full cheeks, big round bright eyes with dark blue-grey irises, an open eager grin, bright blue chin-length bob hair with a soft fringe, light on-camera stage makeup, real skin with fine pores and a few faint freckles on the nose, signature details that must stay: a bright blue chin-length bob, a light grey fedora with a dark wine band, a white shirt with grey suspenders, a light grey fedora with a dark wine band, a white shirt with a tall open collar and sleeves rolled to the forearm, dark grey suspenders with silver clips, black tapered trousers, white leather sneakers, the same shirt-and-suspenders family look as Zhuge Qing, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `zhuge_bai_full.png`
用途：诸葛白（队友）第二步 全身：上传锁定的 zhuge_bai_face.png 生成

上传：图1 = `refs/zhuge_bai_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛白的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体朝右，穿全套舞台服装和鞋，20 岁的成年中国男人，中等个子偏瘦，圆脸；眼睛又大又圆、亮而急切，深蓝灰色虹膜，咧嘴笑；亮蓝色齐下巴波波头；上镜淡妆，皮肤有毛孔，鼻梁上几颗淡雀斑，招牌特征不能丢：亮蓝色波波头 + 浅灰色礼帽（深酒红帽带）+ 白衬衫配灰背带，浅灰色礼帽配深酒红帽带，白色高立领衬衫挽袖，深灰色背带，黑色收脚裤，白球鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned to the right, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, of average height and lean, a round face with full cheeks, big round bright eyes with dark blue-grey irises, an open eager grin, bright blue chin-length bob hair with a soft fringe, light on-camera stage makeup, real skin with fine pores and a few faint freckles on the nose, signature details that must stay: a bright blue chin-length bob, a light grey fedora with a dark wine band, a white shirt with grey suspenders, a light grey fedora with a dark wine band, a white shirt with a tall open collar and sleeves rolled to the forearm, dark grey suspenders with silver clips, black tapered trousers, white leather sneakers, the same shirt-and-suspenders family look as Zhuge Qing, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `zhuge_bai_sheet.png`
用途：诸葛白（队友）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含诸葛白的生成都上传，只认脸，不当画面）

拼图用：`zhuge_bai_face.png`、`zhuge_bai_34.png`、`zhuge_bai_profile.png`、`zhuge_bai_half.png`、`zhuge_bai_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 诸葛家门人（menren）

原创角色，无原作图：第一步用文生图。

### 第一步 原作图 → 真人正面像

#### `menren_face.png`
用途：诸葛家门人（队友）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：不上传图（文生图）

即梦 CN：
```
诸葛家门人的真人综艺定妆照（原创角色，没有原作图，直接文生图），正面头肩像，正对镜头，眼睛平视，28 岁的中国男人，身板宽厚，方脸，眉骨重，小眼睛沉稳，整齐的短胡子；黑发两侧剃短、顶上留短碎发；皮肤毛孔清楚，下巴一道小疤，白色立领衬衫挽袖，藏青色背带，深藏青无袖长马甲（下摆细八卦线），藏青收脚裤，黑靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
front head-and-shoulders portrait facing the camera straight on, eyes level, a 28-year-old Chinese man, broad and solid, a square face with a heavy brow, small calm eyes, a neatly trimmed short beard, black hair shaved short on the sides with a short textured top, real skin with visible pores and a small scar on the chin, a white band-collar shirt with sleeves rolled up, navy suspenders, a sleeveless dark navy long vest with a thin bagua line embroidered at the hem, navy tapered trousers, black boots, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `menren_34.png`
用途：诸葛家门人（队友）第二步 四分之三侧面：上传锁定的 menren_face.png 生成

上传：图1 = `refs/menren_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家门人的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸朝右，28 岁的中国男人，身板宽厚，方脸，眉骨重，小眼睛沉稳，整齐的短胡子；黑发两侧剃短、顶上留短碎发；皮肤毛孔清楚，下巴一道小疤，白色立领衬衫挽袖，藏青色背带，深藏青无袖长马甲（下摆细八卦线），藏青收脚裤，黑靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned to the right, the same person as the omni reference, same face, hairstyle and hair colour, a 28-year-old Chinese man, broad and solid, a square face with a heavy brow, small calm eyes, a neatly trimmed short beard, black hair shaved short on the sides with a short textured top, real skin with visible pores and a small scar on the chin, a white band-collar shirt with sleeves rolled up, navy suspenders, a sleeveless dark navy long vest with a thin bagua line embroidered at the hem, navy tapered trousers, black boots, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `menren_profile.png`
用途：诸葛家门人（队友）第二步 正侧面：上传锁定的 menren_face.png 生成

上传：图1 = `refs/menren_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家门人的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸朝右，看得清侧脸轮廓和发型，28 岁的中国男人，身板宽厚，方脸，眉骨重，小眼睛沉稳，整齐的短胡子；黑发两侧剃短、顶上留短碎发；皮肤毛孔清楚，下巴一道小疤，白色立领衬衫挽袖，藏青色背带，深藏青无袖长马甲（下摆细八卦线），藏青收脚裤，黑靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing to the right, the same person as the omni reference, same face, hairstyle and hair colour, a 28-year-old Chinese man, broad and solid, a square face with a heavy brow, small calm eyes, a neatly trimmed short beard, black hair shaved short on the sides with a short textured top, real skin with visible pores and a small scar on the chin, a white band-collar shirt with sleeves rolled up, navy suspenders, a sleeveless dark navy long vest with a thin bagua line embroidered at the hem, navy tapered trousers, black boots, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `menren_half.png`
用途：诸葛家门人（队友）第二步 半身：上传锁定的 menren_face.png 生成

上传：图1 = `refs/menren_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家门人的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微朝右，穿全套舞台服装，28 岁的中国男人，身板宽厚，方脸，眉骨重，小眼睛沉稳，整齐的短胡子；黑发两侧剃短、顶上留短碎发；皮肤毛孔清楚，下巴一道小疤，白色立领衬衫挽袖，藏青色背带，深藏青无袖长马甲（下摆细八卦线），藏青收脚裤，黑靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly to the right in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a 28-year-old Chinese man, broad and solid, a square face with a heavy brow, small calm eyes, a neatly trimmed short beard, black hair shaved short on the sides with a short textured top, real skin with visible pores and a small scar on the chin, a white band-collar shirt with sleeves rolled up, navy suspenders, a sleeveless dark navy long vest with a thin bagua line embroidered at the hem, navy tapered trousers, black boots, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `menren_expr.png`
用途：诸葛家门人（队友）第二步 表情四宫格：上传锁定的 menren_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/menren_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家门人的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（双手背在身后站得很稳，冲对面抬了抬下巴），四格都是正面头肩，28 岁的中国男人，身板宽厚，方脸，眉骨重，小眼睛沉稳，整齐的短胡子；黑发两侧剃短、顶上留短碎发；皮肤毛孔清楚，下巴一道小疤，白色立领衬衫挽袖，藏青色背带，深藏青无袖长马甲（下摆细八卦线），藏青收脚裤，黑靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 28-year-old Chinese man, broad and solid, a square face with a heavy brow, small calm eyes, a neatly trimmed short beard, black hair shaved short on the sides with a short textured top, real skin with visible pores and a small scar on the chin, a white band-collar shirt with sleeves rolled up, navy suspenders, a sleeveless dark navy long vest with a thin bagua line embroidered at the hem, navy tapered trousers, black boots, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `menren_full.png`
用途：诸葛家门人（队友）第二步 全身：上传锁定的 menren_face.png 生成

上传：图1 = `refs/menren_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家门人的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体朝右，穿全套舞台服装和鞋，28 岁的中国男人，身板宽厚，方脸，眉骨重，小眼睛沉稳，整齐的短胡子；黑发两侧剃短、顶上留短碎发；皮肤毛孔清楚，下巴一道小疤，白色立领衬衫挽袖，藏青色背带，深藏青无袖长马甲（下摆细八卦线），藏青收脚裤，黑靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned to the right, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a 28-year-old Chinese man, broad and solid, a square face with a heavy brow, small calm eyes, a neatly trimmed short beard, black hair shaved short on the sides with a short textured top, real skin with visible pores and a small scar on the chin, a white band-collar shirt with sleeves rolled up, navy suspenders, a sleeveless dark navy long vest with a thin bagua line embroidered at the hem, navy tapered trousers, black boots, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `menren_sheet.png`
用途：诸葛家门人（队友）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含诸葛家门人的生成都上传，只认脸，不当画面）

拼图用：`menren_face.png`、`menren_34.png`、`menren_profile.png`、`menren_half.png`、`menren_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 张楚岚（chulan）

原作图：`refs/canon/zhang_chulan.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/42202)）

原作里的样子：官方图：黑色短发有点乱，刘海碎碎地盖在额头；眼神有点无奈、带点小心思；敞穿深藏青色外套，袖子推到小臂，里面浅灰白T恤，领口和下摆是一圈橙红色；浅蓝色七分裤，裤脚挽起，蓝灰色便鞋。身高 180cm。

### 第一步 原作图 → 真人正面像

#### `chulan_face.png`
用途：张楚岚（队友）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/zhang_chulan.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，23 岁的中国男人，180 厘米，精瘦，窄脸尖下巴，眼睛灵活、带着坏笑，嘴角歪着；乱糟糟的黑色短发，碎刘海盖着额头；上镜淡妆，皮肤有毛孔，鼻头微红，招牌特征不能丢：乱糟糟的黑色短发 + 深藏青外套里露出领口和下摆一圈橙红色的白T恤，敞穿深藏青短夹克，浅灰白T恤配橙红色领口和下摆边，浅蓝色七分阔腿裤，蓝灰便鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 23-year-old Chinese man, 180 cm and wiry, a narrow face with a pointed chin, quick sly dark eyes and a crooked half grin, messy short black hair with choppy bangs over the forehead, styled with matte texture, light on-camera stage makeup, real skin with fine pores and a little redness on the nose, signature details that must stay: messy short black hair, a dark navy open jacket over a white tee with orange-red collar and hem trim, a dark navy cropped bomber-cut jacket worn open with sleeves pushed to the forearm, a light grey-white T-shirt with a bold orange-red ribbed collar and orange-red hem band, light blue cropped wide trousers with rolled cuffs, blue-grey slip-on sneakers, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `chulan_34.png`
用途：张楚岚（队友）第二步 四分之三侧面：上传锁定的 chulan_face.png 生成

上传：图1 = `refs/chulan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张楚岚的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸朝左，23 岁的中国男人，180 厘米，精瘦，窄脸尖下巴，眼睛灵活、带着坏笑，嘴角歪着；乱糟糟的黑色短发，碎刘海盖着额头；上镜淡妆，皮肤有毛孔，鼻头微红，招牌特征不能丢：乱糟糟的黑色短发 + 深藏青外套里露出领口和下摆一圈橙红色的白T恤，敞穿深藏青短夹克，浅灰白T恤配橙红色领口和下摆边，浅蓝色七分阔腿裤，蓝灰便鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 23-year-old Chinese man, 180 cm and wiry, a narrow face with a pointed chin, quick sly dark eyes and a crooked half grin, messy short black hair with choppy bangs over the forehead, styled with matte texture, light on-camera stage makeup, real skin with fine pores and a little redness on the nose, signature details that must stay: messy short black hair, a dark navy open jacket over a white tee with orange-red collar and hem trim, a dark navy cropped bomber-cut jacket worn open with sleeves pushed to the forearm, a light grey-white T-shirt with a bold orange-red ribbed collar and orange-red hem band, light blue cropped wide trousers with rolled cuffs, blue-grey slip-on sneakers, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `chulan_profile.png`
用途：张楚岚（队友）第二步 正侧面：上传锁定的 chulan_face.png 生成

上传：图1 = `refs/chulan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张楚岚的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸朝左，看得清侧脸轮廓和发型，23 岁的中国男人，180 厘米，精瘦，窄脸尖下巴，眼睛灵活、带着坏笑，嘴角歪着；乱糟糟的黑色短发，碎刘海盖着额头；上镜淡妆，皮肤有毛孔，鼻头微红，招牌特征不能丢：乱糟糟的黑色短发 + 深藏青外套里露出领口和下摆一圈橙红色的白T恤，敞穿深藏青短夹克，浅灰白T恤配橙红色领口和下摆边，浅蓝色七分阔腿裤，蓝灰便鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 23-year-old Chinese man, 180 cm and wiry, a narrow face with a pointed chin, quick sly dark eyes and a crooked half grin, messy short black hair with choppy bangs over the forehead, styled with matte texture, light on-camera stage makeup, real skin with fine pores and a little redness on the nose, signature details that must stay: messy short black hair, a dark navy open jacket over a white tee with orange-red collar and hem trim, a dark navy cropped bomber-cut jacket worn open with sleeves pushed to the forearm, a light grey-white T-shirt with a bold orange-red ribbed collar and orange-red hem band, light blue cropped wide trousers with rolled cuffs, blue-grey slip-on sneakers, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `chulan_half.png`
用途：张楚岚（队友）第二步 半身：上传锁定的 chulan_face.png 生成

上传：图1 = `refs/chulan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张楚岚的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微朝左，穿全套舞台服装，23 岁的中国男人，180 厘米，精瘦，窄脸尖下巴，眼睛灵活、带着坏笑，嘴角歪着；乱糟糟的黑色短发，碎刘海盖着额头；上镜淡妆，皮肤有毛孔，鼻头微红，招牌特征不能丢：乱糟糟的黑色短发 + 深藏青外套里露出领口和下摆一圈橙红色的白T恤，敞穿深藏青短夹克，浅灰白T恤配橙红色领口和下摆边，浅蓝色七分阔腿裤，蓝灰便鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly to the left in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a 23-year-old Chinese man, 180 cm and wiry, a narrow face with a pointed chin, quick sly dark eyes and a crooked half grin, messy short black hair with choppy bangs over the forehead, styled with matte texture, light on-camera stage makeup, real skin with fine pores and a little redness on the nose, signature details that must stay: messy short black hair, a dark navy open jacket over a white tee with orange-red collar and hem trim, a dark navy cropped bomber-cut jacket worn open with sleeves pushed to the forearm, a light grey-white T-shirt with a bold orange-red ribbed collar and orange-red hem band, light blue cropped wide trousers with rolled cuffs, blue-grey slip-on sneakers, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `chulan_expr.png`
用途：张楚岚（队友）第二步 表情四宫格：上传锁定的 chulan_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/chulan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张楚岚的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（站在王也身后憋着坏笑，冲对面挤眉弄眼），四格都是正面头肩，23 岁的中国男人，180 厘米，精瘦，窄脸尖下巴，眼睛灵活、带着坏笑，嘴角歪着；乱糟糟的黑色短发，碎刘海盖着额头；上镜淡妆，皮肤有毛孔，鼻头微红，招牌特征不能丢：乱糟糟的黑色短发 + 深藏青外套里露出领口和下摆一圈橙红色的白T恤，敞穿深藏青短夹克，浅灰白T恤配橙红色领口和下摆边，浅蓝色七分阔腿裤，蓝灰便鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 23-year-old Chinese man, 180 cm and wiry, a narrow face with a pointed chin, quick sly dark eyes and a crooked half grin, messy short black hair with choppy bangs over the forehead, styled with matte texture, light on-camera stage makeup, real skin with fine pores and a little redness on the nose, signature details that must stay: messy short black hair, a dark navy open jacket over a white tee with orange-red collar and hem trim, a dark navy cropped bomber-cut jacket worn open with sleeves pushed to the forearm, a light grey-white T-shirt with a bold orange-red ribbed collar and orange-red hem band, light blue cropped wide trousers with rolled cuffs, blue-grey slip-on sneakers, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `chulan_full.png`
用途：张楚岚（队友）第二步 全身：上传锁定的 chulan_face.png 生成

上传：图1 = `refs/chulan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张楚岚的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体朝左，穿全套舞台服装和鞋，23 岁的中国男人，180 厘米，精瘦，窄脸尖下巴，眼睛灵活、带着坏笑，嘴角歪着；乱糟糟的黑色短发，碎刘海盖着额头；上镜淡妆，皮肤有毛孔，鼻头微红，招牌特征不能丢：乱糟糟的黑色短发 + 深藏青外套里露出领口和下摆一圈橙红色的白T恤，敞穿深藏青短夹克，浅灰白T恤配橙红色领口和下摆边，浅蓝色七分阔腿裤，蓝灰便鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned to the left, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a 23-year-old Chinese man, 180 cm and wiry, a narrow face with a pointed chin, quick sly dark eyes and a crooked half grin, messy short black hair with choppy bangs over the forehead, styled with matte texture, light on-camera stage makeup, real skin with fine pores and a little redness on the nose, signature details that must stay: messy short black hair, a dark navy open jacket over a white tee with orange-red collar and hem trim, a dark navy cropped bomber-cut jacket worn open with sleeves pushed to the forearm, a light grey-white T-shirt with a bold orange-red ribbed collar and orange-red hem band, light blue cropped wide trousers with rolled cuffs, blue-grey slip-on sneakers, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `chulan_sheet.png`
用途：张楚岚（队友）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含张楚岚的生成都上传，只认脸，不当画面）

拼图用：`chulan_face.png`、`chulan_34.png`、`chulan_profile.png`、`chulan_half.png`、`chulan_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 武当师弟（daotong）

原创角色，无原作图：第一步用文生图。

### 第一步 原作图 → 真人正面像

#### `daotong_face.png`
用途：武当师弟（队友）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：不上传图（文生图）

即梦 CN：
```
武当师弟的真人综艺定妆照（原创角色，没有原作图，直接文生图），正面头肩像，正对镜头，眼睛平视，20 岁的成年中国男人，又高又瘦，长窄脸，圆眼睛很认真，浓眉；黑发在头顶束成小道髻，插素木簪；皮肤有毛孔，脸颊晒红，灰蓝色交领短外套镶白边，白T恤，灰蓝阔腿裤，白色高帮帆布鞋，浅色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
front head-and-shoulders portrait facing the camera straight on, eyes level, a 20-year-old adult Chinese man, tall and thin with long arms, a long narrow face, earnest round dark eyes, thick eyebrows, black hair tied in a small Taoist topknot with a plain wooden pin, real skin with fine pores and a little sunburn on the cheeks, a grey-blue cropped jacket cut with a Taoist crossed collar and white collar trim, a white T-shirt, loose grey-blue wide trousers, white high-top canvas shoes, a light wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `daotong_34.png`
用途：武当师弟（队友）第二步 四分之三侧面：上传锁定的 daotong_face.png 生成

上传：图1 = `refs/daotong_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是武当师弟的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸朝左，20 岁的成年中国男人，又高又瘦，长窄脸，圆眼睛很认真，浓眉；黑发在头顶束成小道髻，插素木簪；皮肤有毛孔，脸颊晒红，灰蓝色交领短外套镶白边，白T恤，灰蓝阔腿裤，白色高帮帆布鞋，浅色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, tall and thin with long arms, a long narrow face, earnest round dark eyes, thick eyebrows, black hair tied in a small Taoist topknot with a plain wooden pin, real skin with fine pores and a little sunburn on the cheeks, a grey-blue cropped jacket cut with a Taoist crossed collar and white collar trim, a white T-shirt, loose grey-blue wide trousers, white high-top canvas shoes, a light wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `daotong_profile.png`
用途：武当师弟（队友）第二步 正侧面：上传锁定的 daotong_face.png 生成

上传：图1 = `refs/daotong_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是武当师弟的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸朝左，看得清侧脸轮廓和发型，20 岁的成年中国男人，又高又瘦，长窄脸，圆眼睛很认真，浓眉；黑发在头顶束成小道髻，插素木簪；皮肤有毛孔，脸颊晒红，灰蓝色交领短外套镶白边，白T恤，灰蓝阔腿裤，白色高帮帆布鞋，浅色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, tall and thin with long arms, a long narrow face, earnest round dark eyes, thick eyebrows, black hair tied in a small Taoist topknot with a plain wooden pin, real skin with fine pores and a little sunburn on the cheeks, a grey-blue cropped jacket cut with a Taoist crossed collar and white collar trim, a white T-shirt, loose grey-blue wide trousers, white high-top canvas shoes, a light wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `daotong_half.png`
用途：武当师弟（队友）第二步 半身：上传锁定的 daotong_face.png 生成

上传：图1 = `refs/daotong_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是武当师弟的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微朝左，穿全套舞台服装，20 岁的成年中国男人，又高又瘦，长窄脸，圆眼睛很认真，浓眉；黑发在头顶束成小道髻，插素木簪；皮肤有毛孔，脸颊晒红，灰蓝色交领短外套镶白边，白T恤，灰蓝阔腿裤，白色高帮帆布鞋，浅色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly to the left in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, tall and thin with long arms, a long narrow face, earnest round dark eyes, thick eyebrows, black hair tied in a small Taoist topknot with a plain wooden pin, real skin with fine pores and a little sunburn on the cheeks, a grey-blue cropped jacket cut with a Taoist crossed collar and white collar trim, a white T-shirt, loose grey-blue wide trousers, white high-top canvas shoes, a light wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `daotong_expr.png`
用途：武当师弟（队友）第二步 表情四宫格：上传锁定的 daotong_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/daotong_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是武当师弟的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（站在王也身后，站得笔直，一脸认真地跟着点头），四格都是正面头肩，20 岁的成年中国男人，又高又瘦，长窄脸，圆眼睛很认真，浓眉；黑发在头顶束成小道髻，插素木簪；皮肤有毛孔，脸颊晒红，灰蓝色交领短外套镶白边，白T恤，灰蓝阔腿裤，白色高帮帆布鞋，浅色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, tall and thin with long arms, a long narrow face, earnest round dark eyes, thick eyebrows, black hair tied in a small Taoist topknot with a plain wooden pin, real skin with fine pores and a little sunburn on the cheeks, a grey-blue cropped jacket cut with a Taoist crossed collar and white collar trim, a white T-shirt, loose grey-blue wide trousers, white high-top canvas shoes, a light wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `daotong_full.png`
用途：武当师弟（队友）第二步 全身：上传锁定的 daotong_face.png 生成

上传：图1 = `refs/daotong_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是武当师弟的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体朝左，穿全套舞台服装和鞋，20 岁的成年中国男人，又高又瘦，长窄脸，圆眼睛很认真，浓眉；黑发在头顶束成小道髻，插素木簪；皮肤有毛孔，脸颊晒红，灰蓝色交领短外套镶白边，白T恤，灰蓝阔腿裤，白色高帮帆布鞋，浅色木珠手串；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned to the left, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a 20-year-old adult Chinese man, tall and thin with long arms, a long narrow face, earnest round dark eyes, thick eyebrows, black hair tied in a small Taoist topknot with a plain wooden pin, real skin with fine pores and a little sunburn on the cheeks, a grey-blue cropped jacket cut with a Taoist crossed collar and white collar trim, a white T-shirt, loose grey-blue wide trousers, white high-top canvas shoes, a light wooden bead bracelet, plain fabric with no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `daotong_sheet.png`
用途：武当师弟（队友）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含武当师弟的生成都上传，只认脸，不当画面）

拼图用：`daotong_face.png`、`daotong_34.png`、`daotong_profile.png`、`daotong_half.png`、`daotong_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 张之维（tianshi）

原作图：`refs/canon/zhang_zhiwei.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/103754)）

原作里的样子：官方图：灰白色长发往后梳，在脑后束起，头顶有个小髻，几缕长发垂在脸边；浓密的白眉，长长的白胡子和八字胡；脸上皱纹很深，眼皮下垂；身穿深色道袍，领口是灰色暗纹缎面宽领，里面露出白色内领。身高 187cm。

### 第一步 原作图 → 真人正面像

#### `tianshi_face.png`
用途：张之维（评委）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/zhang_zhiwei.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，看上去约 90 岁的中国老人，身高 187 厘米，腰板笔直；灰白长发往后梳、在脑后束起，头顶一个小髻；浓白眉，长长的白胡子；笑纹很深，眼睛亮而带笑；皮肤有皱纹和老年斑，招牌特征不能丢：束在脑后的灰白长发 + 长长的白胡子 + 深色道袍的灰色暗纹宽领，剪裁挺括的黑色长道袍，灰色提花云纹宽领，露出白色内领，黑布腰带，黑布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a Chinese man who looks about 90, tall at 187 cm and upright, long grey-white hair combed back and tied behind the head with a small topknot and a few long strands at the temples, thick white eyebrows, a long flowing white beard and moustache, deep laugh lines, heavy eyelids over bright amused eyes, weathered skin with wrinkles and age spots, signature details that must stay: long grey-white hair tied back with a small topknot, a long white beard and moustache, a dark robe with a wide grey patterned collar, a sharply tailored long black Taoist robe in heavy matte silk with a wide grey jacquard cloud-pattern collar over a white inner collar, a black cloth belt, black cloth shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `tianshi_34.png`
用途：张之维（评委）第二步 四分之三侧面：上传锁定的 tianshi_face.png 生成

上传：图1 = `refs/tianshi_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张之维的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，看上去约 90 岁的中国老人，身高 187 厘米，腰板笔直；灰白长发往后梳、在脑后束起，头顶一个小髻；浓白眉，长长的白胡子；笑纹很深，眼睛亮而带笑；皮肤有皱纹和老年斑，招牌特征不能丢：束在脑后的灰白长发 + 长长的白胡子 + 深色道袍的灰色暗纹宽领，剪裁挺括的黑色长道袍，灰色提花云纹宽领，露出白色内领，黑布腰带，黑布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 90, tall at 187 cm and upright, long grey-white hair combed back and tied behind the head with a small topknot and a few long strands at the temples, thick white eyebrows, a long flowing white beard and moustache, deep laugh lines, heavy eyelids over bright amused eyes, weathered skin with wrinkles and age spots, signature details that must stay: long grey-white hair tied back with a small topknot, a long white beard and moustache, a dark robe with a wide grey patterned collar, a sharply tailored long black Taoist robe in heavy matte silk with a wide grey jacquard cloud-pattern collar over a white inner collar, a black cloth belt, black cloth shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `tianshi_profile.png`
用途：张之维（评委）第二步 正侧面：上传锁定的 tianshi_face.png 生成

上传：图1 = `refs/tianshi_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张之维的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，看上去约 90 岁的中国老人，身高 187 厘米，腰板笔直；灰白长发往后梳、在脑后束起，头顶一个小髻；浓白眉，长长的白胡子；笑纹很深，眼睛亮而带笑；皮肤有皱纹和老年斑，招牌特征不能丢：束在脑后的灰白长发 + 长长的白胡子 + 深色道袍的灰色暗纹宽领，剪裁挺括的黑色长道袍，灰色提花云纹宽领，露出白色内领，黑布腰带，黑布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 90, tall at 187 cm and upright, long grey-white hair combed back and tied behind the head with a small topknot and a few long strands at the temples, thick white eyebrows, a long flowing white beard and moustache, deep laugh lines, heavy eyelids over bright amused eyes, weathered skin with wrinkles and age spots, signature details that must stay: long grey-white hair tied back with a small topknot, a long white beard and moustache, a dark robe with a wide grey patterned collar, a sharply tailored long black Taoist robe in heavy matte silk with a wide grey jacquard cloud-pattern collar over a white inner collar, a black cloth belt, black cloth shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `tianshi_half.png`
用途：张之维（评委）第二步 半身：上传锁定的 tianshi_face.png 生成

上传：图1 = `refs/tianshi_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张之维的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，看上去约 90 岁的中国老人，身高 187 厘米，腰板笔直；灰白长发往后梳、在脑后束起，头顶一个小髻；浓白眉，长长的白胡子；笑纹很深，眼睛亮而带笑；皮肤有皱纹和老年斑，招牌特征不能丢：束在脑后的灰白长发 + 长长的白胡子 + 深色道袍的灰色暗纹宽领，剪裁挺括的黑色长道袍，灰色提花云纹宽领，露出白色内领，黑布腰带，黑布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 90, tall at 187 cm and upright, long grey-white hair combed back and tied behind the head with a small topknot and a few long strands at the temples, thick white eyebrows, a long flowing white beard and moustache, deep laugh lines, heavy eyelids over bright amused eyes, weathered skin with wrinkles and age spots, signature details that must stay: long grey-white hair tied back with a small topknot, a long white beard and moustache, a dark robe with a wide grey patterned collar, a sharply tailored long black Taoist robe in heavy matte silk with a wide grey jacquard cloud-pattern collar over a white inner collar, a black cloth belt, black cloth shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `tianshi_expr.png`
用途：张之维（评委）第二步 表情四宫格：上传锁定的 tianshi_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/tianshi_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张之维的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（坐在王座上捋着白胡子，眯眼笑着点了一下头），四格都是正面头肩，看上去约 90 岁的中国老人，身高 187 厘米，腰板笔直；灰白长发往后梳、在脑后束起，头顶一个小髻；浓白眉，长长的白胡子；笑纹很深，眼睛亮而带笑；皮肤有皱纹和老年斑，招牌特征不能丢：束在脑后的灰白长发 + 长长的白胡子 + 深色道袍的灰色暗纹宽领，剪裁挺括的黑色长道袍，灰色提花云纹宽领，露出白色内领，黑布腰带，黑布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 90, tall at 187 cm and upright, long grey-white hair combed back and tied behind the head with a small topknot and a few long strands at the temples, thick white eyebrows, a long flowing white beard and moustache, deep laugh lines, heavy eyelids over bright amused eyes, weathered skin with wrinkles and age spots, signature details that must stay: long grey-white hair tied back with a small topknot, a long white beard and moustache, a dark robe with a wide grey patterned collar, a sharply tailored long black Taoist robe in heavy matte silk with a wide grey jacquard cloud-pattern collar over a white inner collar, a black cloth belt, black cloth shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `tianshi_full.png`
用途：张之维（评委）第二步 全身：上传锁定的 tianshi_face.png 生成

上传：图1 = `refs/tianshi_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张之维的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，看上去约 90 岁的中国老人，身高 187 厘米，腰板笔直；灰白长发往后梳、在脑后束起，头顶一个小髻；浓白眉，长长的白胡子；笑纹很深，眼睛亮而带笑；皮肤有皱纹和老年斑，招牌特征不能丢：束在脑后的灰白长发 + 长长的白胡子 + 深色道袍的灰色暗纹宽领，剪裁挺括的黑色长道袍，灰色提花云纹宽领，露出白色内领，黑布腰带，黑布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 90, tall at 187 cm and upright, long grey-white hair combed back and tied behind the head with a small topknot and a few long strands at the temples, thick white eyebrows, a long flowing white beard and moustache, deep laugh lines, heavy eyelids over bright amused eyes, weathered skin with wrinkles and age spots, signature details that must stay: long grey-white hair tied back with a small topknot, a long white beard and moustache, a dark robe with a wide grey patterned collar, a sharply tailored long black Taoist robe in heavy matte silk with a wide grey jacquard cloud-pattern collar over a white inner collar, a black cloth belt, black cloth shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `tianshi_sheet.png`
用途：张之维（评委）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含张之维的生成都上传，只认脸，不当画面）

拼图用：`tianshi_face.png`、`tianshi_34.png`、`tianshi_profile.png`、`tianshi_half.png`、`tianshi_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 陆瑾（lu_jin）

原作图：`refs/canon/lu_jin.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/103755)）

原作里的样子：官方图：白色长发从中间分开、直直披到肩膀以下；浓白眉，白色八字胡连着下巴上一撮白胡子；表情严肃，眉头紧锁；穿黑色西装外套和白衬衫，正在整理领口。身高 187cm。

### 第一步 原作图 → 真人正面像

#### `lu_jin_face.png`
用途：陆瑾（评委）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/lu_jin.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，看上去约 88 岁的中国老人，身高 187 厘米，背挺得笔直，长脸，眉头紧锁；浓白眉；白色长直发中分、披到肩下；白八字胡连着下巴尖白胡子；眼眶容易泛红；皮肤有深皱纹和老年斑，招牌特征不能丢：披到肩下的白色长发 + 白色八字胡和下巴白胡子 + 黑西装白衬衫，剪裁利落的黑色长款西装，白衬衫扣到领口、不打领带，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a Chinese man who looks about 88, tall at 187 cm and straight-backed, a long stern face with a knitted brow, thick white eyebrows, long straight white hair parted in the middle and falling past the shoulders, a white moustache joined to a pointed white chin beard, watery eyes that tear up easily, weathered skin with deep wrinkles and age spots, signature details that must stay: long straight white hair past the shoulders, a white moustache joined to a white chin beard, a black suit with a white shirt, a sharply tailored black suit with a long jacket, a crisp white shirt buttoned to the collar with no tie, a black silk pocket square, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `lu_jin_34.png`
用途：陆瑾（评委）第二步 四分之三侧面：上传锁定的 lu_jin_face.png 生成

上传：图1 = `refs/lu_jin_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是陆瑾的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，看上去约 88 岁的中国老人，身高 187 厘米，背挺得笔直，长脸，眉头紧锁；浓白眉；白色长直发中分、披到肩下；白八字胡连着下巴尖白胡子；眼眶容易泛红；皮肤有深皱纹和老年斑，招牌特征不能丢：披到肩下的白色长发 + 白色八字胡和下巴白胡子 + 黑西装白衬衫，剪裁利落的黑色长款西装，白衬衫扣到领口、不打领带，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 88, tall at 187 cm and straight-backed, a long stern face with a knitted brow, thick white eyebrows, long straight white hair parted in the middle and falling past the shoulders, a white moustache joined to a pointed white chin beard, watery eyes that tear up easily, weathered skin with deep wrinkles and age spots, signature details that must stay: long straight white hair past the shoulders, a white moustache joined to a white chin beard, a black suit with a white shirt, a sharply tailored black suit with a long jacket, a crisp white shirt buttoned to the collar with no tie, a black silk pocket square, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `lu_jin_profile.png`
用途：陆瑾（评委）第二步 正侧面：上传锁定的 lu_jin_face.png 生成

上传：图1 = `refs/lu_jin_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是陆瑾的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，看上去约 88 岁的中国老人，身高 187 厘米，背挺得笔直，长脸，眉头紧锁；浓白眉；白色长直发中分、披到肩下；白八字胡连着下巴尖白胡子；眼眶容易泛红；皮肤有深皱纹和老年斑，招牌特征不能丢：披到肩下的白色长发 + 白色八字胡和下巴白胡子 + 黑西装白衬衫，剪裁利落的黑色长款西装，白衬衫扣到领口、不打领带，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 88, tall at 187 cm and straight-backed, a long stern face with a knitted brow, thick white eyebrows, long straight white hair parted in the middle and falling past the shoulders, a white moustache joined to a pointed white chin beard, watery eyes that tear up easily, weathered skin with deep wrinkles and age spots, signature details that must stay: long straight white hair past the shoulders, a white moustache joined to a white chin beard, a black suit with a white shirt, a sharply tailored black suit with a long jacket, a crisp white shirt buttoned to the collar with no tie, a black silk pocket square, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `lu_jin_half.png`
用途：陆瑾（评委）第二步 半身：上传锁定的 lu_jin_face.png 生成

上传：图1 = `refs/lu_jin_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是陆瑾的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，看上去约 88 岁的中国老人，身高 187 厘米，背挺得笔直，长脸，眉头紧锁；浓白眉；白色长直发中分、披到肩下；白八字胡连着下巴尖白胡子；眼眶容易泛红；皮肤有深皱纹和老年斑，招牌特征不能丢：披到肩下的白色长发 + 白色八字胡和下巴白胡子 + 黑西装白衬衫，剪裁利落的黑色长款西装，白衬衫扣到领口、不打领带，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 88, tall at 187 cm and straight-backed, a long stern face with a knitted brow, thick white eyebrows, long straight white hair parted in the middle and falling past the shoulders, a white moustache joined to a pointed white chin beard, watery eyes that tear up easily, weathered skin with deep wrinkles and age spots, signature details that must stay: long straight white hair past the shoulders, a white moustache joined to a white chin beard, a black suit with a white shirt, a sharply tailored black suit with a long jacket, a crisp white shirt buttoned to the collar with no tie, a black silk pocket square, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `lu_jin_expr.png`
用途：陆瑾（评委）第二步 表情四宫格：上传锁定的 lu_jin_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/lu_jin_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是陆瑾的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（坐在王座上眼眶一下红了，拿白手帕擦眼泪，又板起脸装没事），四格都是正面头肩，看上去约 88 岁的中国老人，身高 187 厘米，背挺得笔直，长脸，眉头紧锁；浓白眉；白色长直发中分、披到肩下；白八字胡连着下巴尖白胡子；眼眶容易泛红；皮肤有深皱纹和老年斑，招牌特征不能丢：披到肩下的白色长发 + 白色八字胡和下巴白胡子 + 黑西装白衬衫，剪裁利落的黑色长款西装，白衬衫扣到领口、不打领带，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 88, tall at 187 cm and straight-backed, a long stern face with a knitted brow, thick white eyebrows, long straight white hair parted in the middle and falling past the shoulders, a white moustache joined to a pointed white chin beard, watery eyes that tear up easily, weathered skin with deep wrinkles and age spots, signature details that must stay: long straight white hair past the shoulders, a white moustache joined to a white chin beard, a black suit with a white shirt, a sharply tailored black suit with a long jacket, a crisp white shirt buttoned to the collar with no tie, a black silk pocket square, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `lu_jin_full.png`
用途：陆瑾（评委）第二步 全身：上传锁定的 lu_jin_face.png 生成

上传：图1 = `refs/lu_jin_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是陆瑾的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，看上去约 88 岁的中国老人，身高 187 厘米，背挺得笔直，长脸，眉头紧锁；浓白眉；白色长直发中分、披到肩下；白八字胡连着下巴尖白胡子；眼眶容易泛红；皮肤有深皱纹和老年斑，招牌特征不能丢：披到肩下的白色长发 + 白色八字胡和下巴白胡子 + 黑西装白衬衫，剪裁利落的黑色长款西装，白衬衫扣到领口、不打领带，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese man who looks about 88, tall at 187 cm and straight-backed, a long stern face with a knitted brow, thick white eyebrows, long straight white hair parted in the middle and falling past the shoulders, a white moustache joined to a pointed white chin beard, watery eyes that tear up easily, weathered skin with deep wrinkles and age spots, signature details that must stay: long straight white hair past the shoulders, a white moustache joined to a white chin beard, a black suit with a white shirt, a sharply tailored black suit with a long jacket, a crisp white shirt buttoned to the collar with no tie, a black silk pocket square, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `lu_jin_sheet.png`
用途：陆瑾（评委）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含陆瑾的生成都上传，只认脸，不当画面）

拼图用：`lu_jin_face.png`、`lu_jin_34.png`、`lu_jin_profile.png`、`lu_jin_half.png`、`lu_jin_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 风正豪（feng_zhenghao）

原作图：`refs/canon/feng_zhenghao.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/45136)）

原作里的样子：官方图：灰白色短发整齐往后梳成背头；戴圆形细金属框眼镜；胡子刮净，笑容精明；深蓝底白色小圆点衬衫，外面深灰蓝色西装外套，腰间一条深色宽腰封。

### 第一步 原作图 → 真人正面像

#### `feng_zhenghao_face.png`
用途：风正豪（评委）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/feng_zhenghao.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，50 岁的中国男人，肩宽，方脸，下颌有力；戴圆形细金属框眼镜，眼神精明；灰白色短发往后梳成背头；胡子刮净，嘴角一抹心里有数的笑；皮肤有毛孔，眼角细纹，招牌特征不能丢：圆形细金属框眼镜 + 灰白背头 + 深蓝底白点衬衫，深蓝色真丝衬衫印白色小圆点，深石板蓝双排扣西装外套，黑色宽腰封，深色西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 50-year-old Chinese man, broad-shouldered and well kept, a square face with a firm jaw, sharp shrewd eyes behind round thin wire-rimmed glasses, grey-white short hair slicked straight back, clean-shaven, a knowing smile, real skin with pores and fine lines around the eyes, signature details that must stay: round thin wire-rimmed glasses, grey-white slicked-back hair, a deep blue shirt with small white polka dots, a deep blue silk shirt with small white polka dots buttoned to the neck, a tailored dark slate-blue double-breasted suit jacket, a wide black cummerbund-style sash at the waist, dark trousers, polished black shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `feng_zhenghao_34.png`
用途：风正豪（评委）第二步 四分之三侧面：上传锁定的 feng_zhenghao_face.png 生成

上传：图1 = `refs/feng_zhenghao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风正豪的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，50 岁的中国男人，肩宽，方脸，下颌有力；戴圆形细金属框眼镜，眼神精明；灰白色短发往后梳成背头；胡子刮净，嘴角一抹心里有数的笑；皮肤有毛孔，眼角细纹，招牌特征不能丢：圆形细金属框眼镜 + 灰白背头 + 深蓝底白点衬衫，深蓝色真丝衬衫印白色小圆点，深石板蓝双排扣西装外套，黑色宽腰封，深色西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 50-year-old Chinese man, broad-shouldered and well kept, a square face with a firm jaw, sharp shrewd eyes behind round thin wire-rimmed glasses, grey-white short hair slicked straight back, clean-shaven, a knowing smile, real skin with pores and fine lines around the eyes, signature details that must stay: round thin wire-rimmed glasses, grey-white slicked-back hair, a deep blue shirt with small white polka dots, a deep blue silk shirt with small white polka dots buttoned to the neck, a tailored dark slate-blue double-breasted suit jacket, a wide black cummerbund-style sash at the waist, dark trousers, polished black shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `feng_zhenghao_profile.png`
用途：风正豪（评委）第二步 正侧面：上传锁定的 feng_zhenghao_face.png 生成

上传：图1 = `refs/feng_zhenghao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风正豪的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，50 岁的中国男人，肩宽，方脸，下颌有力；戴圆形细金属框眼镜，眼神精明；灰白色短发往后梳成背头；胡子刮净，嘴角一抹心里有数的笑；皮肤有毛孔，眼角细纹，招牌特征不能丢：圆形细金属框眼镜 + 灰白背头 + 深蓝底白点衬衫，深蓝色真丝衬衫印白色小圆点，深石板蓝双排扣西装外套，黑色宽腰封，深色西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 50-year-old Chinese man, broad-shouldered and well kept, a square face with a firm jaw, sharp shrewd eyes behind round thin wire-rimmed glasses, grey-white short hair slicked straight back, clean-shaven, a knowing smile, real skin with pores and fine lines around the eyes, signature details that must stay: round thin wire-rimmed glasses, grey-white slicked-back hair, a deep blue shirt with small white polka dots, a deep blue silk shirt with small white polka dots buttoned to the neck, a tailored dark slate-blue double-breasted suit jacket, a wide black cummerbund-style sash at the waist, dark trousers, polished black shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `feng_zhenghao_half.png`
用途：风正豪（评委）第二步 半身：上传锁定的 feng_zhenghao_face.png 生成

上传：图1 = `refs/feng_zhenghao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风正豪的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，50 岁的中国男人，肩宽，方脸，下颌有力；戴圆形细金属框眼镜，眼神精明；灰白色短发往后梳成背头；胡子刮净，嘴角一抹心里有数的笑；皮肤有毛孔，眼角细纹，招牌特征不能丢：圆形细金属框眼镜 + 灰白背头 + 深蓝底白点衬衫，深蓝色真丝衬衫印白色小圆点，深石板蓝双排扣西装外套，黑色宽腰封，深色西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a 50-year-old Chinese man, broad-shouldered and well kept, a square face with a firm jaw, sharp shrewd eyes behind round thin wire-rimmed glasses, grey-white short hair slicked straight back, clean-shaven, a knowing smile, real skin with pores and fine lines around the eyes, signature details that must stay: round thin wire-rimmed glasses, grey-white slicked-back hair, a deep blue shirt with small white polka dots, a deep blue silk shirt with small white polka dots buttoned to the neck, a tailored dark slate-blue double-breasted suit jacket, a wide black cummerbund-style sash at the waist, dark trousers, polished black shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `feng_zhenghao_expr.png`
用途：风正豪（评委）第二步 表情四宫格：上传锁定的 feng_zhenghao_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/feng_zhenghao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风正豪的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（坐在王座上十指交叉，眉毛一挑，嘴角绷住不笑），四格都是正面头肩，50 岁的中国男人，肩宽，方脸，下颌有力；戴圆形细金属框眼镜，眼神精明；灰白色短发往后梳成背头；胡子刮净，嘴角一抹心里有数的笑；皮肤有毛孔，眼角细纹，招牌特征不能丢：圆形细金属框眼镜 + 灰白背头 + 深蓝底白点衬衫，深蓝色真丝衬衫印白色小圆点，深石板蓝双排扣西装外套，黑色宽腰封，深色西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 50-year-old Chinese man, broad-shouldered and well kept, a square face with a firm jaw, sharp shrewd eyes behind round thin wire-rimmed glasses, grey-white short hair slicked straight back, clean-shaven, a knowing smile, real skin with pores and fine lines around the eyes, signature details that must stay: round thin wire-rimmed glasses, grey-white slicked-back hair, a deep blue shirt with small white polka dots, a deep blue silk shirt with small white polka dots buttoned to the neck, a tailored dark slate-blue double-breasted suit jacket, a wide black cummerbund-style sash at the waist, dark trousers, polished black shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `feng_zhenghao_full.png`
用途：风正豪（评委）第二步 全身：上传锁定的 feng_zhenghao_face.png 生成

上传：图1 = `refs/feng_zhenghao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风正豪的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，50 岁的中国男人，肩宽，方脸，下颌有力；戴圆形细金属框眼镜，眼神精明；灰白色短发往后梳成背头；胡子刮净，嘴角一抹心里有数的笑；皮肤有毛孔，眼角细纹，招牌特征不能丢：圆形细金属框眼镜 + 灰白背头 + 深蓝底白点衬衫，深蓝色真丝衬衫印白色小圆点，深石板蓝双排扣西装外套，黑色宽腰封，深色西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a 50-year-old Chinese man, broad-shouldered and well kept, a square face with a firm jaw, sharp shrewd eyes behind round thin wire-rimmed glasses, grey-white short hair slicked straight back, clean-shaven, a knowing smile, real skin with pores and fine lines around the eyes, signature details that must stay: round thin wire-rimmed glasses, grey-white slicked-back hair, a deep blue shirt with small white polka dots, a deep blue silk shirt with small white polka dots buttoned to the neck, a tailored dark slate-blue double-breasted suit jacket, a wide black cummerbund-style sash at the waist, dark trousers, polished black shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `feng_zhenghao_sheet.png`
用途：风正豪（评委）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含风正豪的生成都上传，只认脸，不当画面）

拼图用：`feng_zhenghao_face.png`、`feng_zhenghao_34.png`、`feng_zhenghao_profile.png`、`feng_zhenghao_half.png`、`feng_zhenghao_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 徐四（xu_si）

原作图：`refs/canon/xu_si.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/42205)）

原作里的样子：官方图：银白色短发蓬乱，往一边拨；下巴一撮山羊胡加淡胡茬；眼神懒散带痞气；敞穿卡其色夹克，领口两侧各有一道金色短条，里面白色宽领T恤；深棕灰色七分裤，棕色皮鞋；一只手插在裤兜里。没有戴墨镜。

### 第一步 原作图 → 真人正面像

#### `xu_si_face.png`
用途：徐四（主持）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/xu_si.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，36 岁的中国男人，瘦长微弓背，长脸，颧骨突出；下巴一撮山羊胡加淡胡茬，嘴角歪着痞笑；银白色短发蓬乱、往一边拨；眼角有倦纹，皮肤有毛孔，招牌特征不能丢：银白色蓬乱短发 + 下巴山羊胡 + 卡其色夹克（领口金色短条），敞穿卡其色宽版工装夹克（领尖两道金色短条），白色宽领T恤，深棕灰七分裤，棕皮鞋，细银链；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 36-year-old Chinese man, lanky with a slight hunch, a long bony face, a small chin goatee with light stubble, a cocky lopsided smirk, messy silver-white short hair swept to one side, tired creased eyes, real skin with pores, signature details that must stay: messy silver-white short hair, a small chin goatee with stubble, a khaki jacket with two small gold bars on the collar, a boxy khaki cotton work jacket worn open with two small gold bars on the collar points, a loose white scoop-neck T-shirt, dark brown-grey cropped trousers, brown leather shoes, a thin silver chain, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `xu_si_34.png`
用途：徐四（主持）第二步 四分之三侧面：上传锁定的 xu_si_face.png 生成

上传：图1 = `refs/xu_si_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐四的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，36 岁的中国男人，瘦长微弓背，长脸，颧骨突出；下巴一撮山羊胡加淡胡茬，嘴角歪着痞笑；银白色短发蓬乱、往一边拨；眼角有倦纹，皮肤有毛孔，招牌特征不能丢：银白色蓬乱短发 + 下巴山羊胡 + 卡其色夹克（领口金色短条），敞穿卡其色宽版工装夹克（领尖两道金色短条），白色宽领T恤，深棕灰七分裤，棕皮鞋，细银链；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 36-year-old Chinese man, lanky with a slight hunch, a long bony face, a small chin goatee with light stubble, a cocky lopsided smirk, messy silver-white short hair swept to one side, tired creased eyes, real skin with pores, signature details that must stay: messy silver-white short hair, a small chin goatee with stubble, a khaki jacket with two small gold bars on the collar, a boxy khaki cotton work jacket worn open with two small gold bars on the collar points, a loose white scoop-neck T-shirt, dark brown-grey cropped trousers, brown leather shoes, a thin silver chain, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `xu_si_profile.png`
用途：徐四（主持）第二步 正侧面：上传锁定的 xu_si_face.png 生成

上传：图1 = `refs/xu_si_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐四的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，36 岁的中国男人，瘦长微弓背，长脸，颧骨突出；下巴一撮山羊胡加淡胡茬，嘴角歪着痞笑；银白色短发蓬乱、往一边拨；眼角有倦纹，皮肤有毛孔，招牌特征不能丢：银白色蓬乱短发 + 下巴山羊胡 + 卡其色夹克（领口金色短条），敞穿卡其色宽版工装夹克（领尖两道金色短条），白色宽领T恤，深棕灰七分裤，棕皮鞋，细银链；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 36-year-old Chinese man, lanky with a slight hunch, a long bony face, a small chin goatee with light stubble, a cocky lopsided smirk, messy silver-white short hair swept to one side, tired creased eyes, real skin with pores, signature details that must stay: messy silver-white short hair, a small chin goatee with stubble, a khaki jacket with two small gold bars on the collar, a boxy khaki cotton work jacket worn open with two small gold bars on the collar points, a loose white scoop-neck T-shirt, dark brown-grey cropped trousers, brown leather shoes, a thin silver chain, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `xu_si_half.png`
用途：徐四（主持）第二步 半身：上传锁定的 xu_si_face.png 生成

上传：图1 = `refs/xu_si_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐四的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，右手拿着银色有线话筒，话筒在嘴的斜下方，36 岁的中国男人，瘦长微弓背，长脸，颧骨突出；下巴一撮山羊胡加淡胡茬，嘴角歪着痞笑；银白色短发蓬乱、往一边拨；眼角有倦纹，皮肤有毛孔，招牌特征不能丢：银白色蓬乱短发 + 下巴山羊胡 + 卡其色夹克（领口金色短条），敞穿卡其色宽版工装夹克（领尖两道金色短条），白色宽领T恤，深棕灰七分裤，棕皮鞋，细银链；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 36-year-old Chinese man, lanky with a slight hunch, a long bony face, a small chin goatee with light stubble, a cocky lopsided smirk, messy silver-white short hair swept to one side, tired creased eyes, real skin with pores, signature details that must stay: messy silver-white short hair, a small chin goatee with stubble, a khaki jacket with two small gold bars on the collar, a boxy khaki cotton work jacket worn open with two small gold bars on the collar points, a loose white scoop-neck T-shirt, dark brown-grey cropped trousers, brown leather shoes, a thin silver chain, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `xu_si_expr.png`
用途：徐四（主持）第二步 表情四宫格：上传锁定的 xu_si_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/xu_si_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐四的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（靠在DJ台边上挂着痞笑，跟着节奏晃脑袋），四格都是正面头肩，36 岁的中国男人，瘦长微弓背，长脸，颧骨突出；下巴一撮山羊胡加淡胡茬，嘴角歪着痞笑；银白色短发蓬乱、往一边拨；眼角有倦纹，皮肤有毛孔，招牌特征不能丢：银白色蓬乱短发 + 下巴山羊胡 + 卡其色夹克（领口金色短条），敞穿卡其色宽版工装夹克（领尖两道金色短条），白色宽领T恤，深棕灰七分裤，棕皮鞋，细银链；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 36-year-old Chinese man, lanky with a slight hunch, a long bony face, a small chin goatee with light stubble, a cocky lopsided smirk, messy silver-white short hair swept to one side, tired creased eyes, real skin with pores, signature details that must stay: messy silver-white short hair, a small chin goatee with stubble, a khaki jacket with two small gold bars on the collar, a boxy khaki cotton work jacket worn open with two small gold bars on the collar points, a loose white scoop-neck T-shirt, dark brown-grey cropped trousers, brown leather shoes, a thin silver chain, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `xu_si_full.png`
用途：徐四（主持）第二步 全身：上传锁定的 xu_si_face.png 生成

上传：图1 = `refs/xu_si_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐四的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，右手拿着银色有线话筒，话筒在嘴的斜下方，36 岁的中国男人，瘦长微弓背，长脸，颧骨突出；下巴一撮山羊胡加淡胡茬，嘴角歪着痞笑；银白色短发蓬乱、往一边拨；眼角有倦纹，皮肤有毛孔，招牌特征不能丢：银白色蓬乱短发 + 下巴山羊胡 + 卡其色夹克（领口金色短条），敞穿卡其色宽版工装夹克（领尖两道金色短条），白色宽领T恤，深棕灰七分裤，棕皮鞋，细银链；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 36-year-old Chinese man, lanky with a slight hunch, a long bony face, a small chin goatee with light stubble, a cocky lopsided smirk, messy silver-white short hair swept to one side, tired creased eyes, real skin with pores, signature details that must stay: messy silver-white short hair, a small chin goatee with stubble, a khaki jacket with two small gold bars on the collar, a boxy khaki cotton work jacket worn open with two small gold bars on the collar points, a loose white scoop-neck T-shirt, dark brown-grey cropped trousers, brown leather shoes, a thin silver chain, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `xu_si_sheet.png`
用途：徐四（主持）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含徐四的生成都上传，只认脸，不当画面）

拼图用：`xu_si_face.png`、`xu_si_34.png`、`xu_si_profile.png`、`xu_si_half.png`、`xu_si_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 徐三（xu_san）

原作图：`refs/canon/xu_san.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/42204)）

原作里的样子：官方图：黑色短发，刘海碎碎地垂在额前；戴细框长方形眼镜；表情平静；黑色西装外套敞着，白衬衫领口敞开不打领带，黑色西裤，黑皮带，黑皮鞋；一只手插在裤兜里。

### 第一步 原作图 → 真人正面像

#### `xu_san_face.png`
用途：徐三（DJ）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/xu_san.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，38 岁的中国男人，中等身材，神情沉稳，戴细框长方形眼镜；黑色短发，碎刘海垂在额前；胡子刮净有淡青色，嘴角半笑；皮肤有毛孔，额头细纹，招牌特征不能丢：细框长方形眼镜 + 黑色短发碎刘海 + 黑西装配敞领白衬衫，修身黑西装外套推着袖子，白衬衫敞领不打领带，黑西裤，脖子上挂一副黑色大耳机；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 38-year-old Chinese man, medium build, a calm oval face, thin rectangular glasses, short black hair with a light choppy fringe over the forehead, clean-shaven with a faint shadow, a composed half smile, real skin with pores and fine lines on the forehead, signature details that must stay: thin rectangular glasses, short black hair with a light fringe, a black suit over an open-collar white shirt, a slim black suit jacket with the sleeves pushed up, a white shirt with the collar open and no tie, black trousers, a black leather belt, large black headphones around his neck, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `xu_san_34.png`
用途：徐三（DJ）第二步 四分之三侧面：上传锁定的 xu_san_face.png 生成

上传：图1 = `refs/xu_san_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐三的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，38 岁的中国男人，中等身材，神情沉稳，戴细框长方形眼镜；黑色短发，碎刘海垂在额前；胡子刮净有淡青色，嘴角半笑；皮肤有毛孔，额头细纹，招牌特征不能丢：细框长方形眼镜 + 黑色短发碎刘海 + 黑西装配敞领白衬衫，修身黑西装外套推着袖子，白衬衫敞领不打领带，黑西裤，脖子上挂一副黑色大耳机；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 38-year-old Chinese man, medium build, a calm oval face, thin rectangular glasses, short black hair with a light choppy fringe over the forehead, clean-shaven with a faint shadow, a composed half smile, real skin with pores and fine lines on the forehead, signature details that must stay: thin rectangular glasses, short black hair with a light fringe, a black suit over an open-collar white shirt, a slim black suit jacket with the sleeves pushed up, a white shirt with the collar open and no tie, black trousers, a black leather belt, large black headphones around his neck, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `xu_san_profile.png`
用途：徐三（DJ）第二步 正侧面：上传锁定的 xu_san_face.png 生成

上传：图1 = `refs/xu_san_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐三的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，38 岁的中国男人，中等身材，神情沉稳，戴细框长方形眼镜；黑色短发，碎刘海垂在额前；胡子刮净有淡青色，嘴角半笑；皮肤有毛孔，额头细纹，招牌特征不能丢：细框长方形眼镜 + 黑色短发碎刘海 + 黑西装配敞领白衬衫，修身黑西装外套推着袖子，白衬衫敞领不打领带，黑西裤，脖子上挂一副黑色大耳机；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 38-year-old Chinese man, medium build, a calm oval face, thin rectangular glasses, short black hair with a light choppy fringe over the forehead, clean-shaven with a faint shadow, a composed half smile, real skin with pores and fine lines on the forehead, signature details that must stay: thin rectangular glasses, short black hair with a light fringe, a black suit over an open-collar white shirt, a slim black suit jacket with the sleeves pushed up, a white shirt with the collar open and no tie, black trousers, a black leather belt, large black headphones around his neck, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `xu_san_half.png`
用途：徐三（DJ）第二步 半身：上传锁定的 xu_san_face.png 生成

上传：图1 = `refs/xu_san_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐三的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，右手拿着银色有线话筒，话筒在嘴的斜下方，38 岁的中国男人，中等身材，神情沉稳，戴细框长方形眼镜；黑色短发，碎刘海垂在额前；胡子刮净有淡青色，嘴角半笑；皮肤有毛孔，额头细纹，招牌特征不能丢：细框长方形眼镜 + 黑色短发碎刘海 + 黑西装配敞领白衬衫，修身黑西装外套推着袖子，白衬衫敞领不打领带，黑西裤，脖子上挂一副黑色大耳机；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 38-year-old Chinese man, medium build, a calm oval face, thin rectangular glasses, short black hair with a light choppy fringe over the forehead, clean-shaven with a faint shadow, a composed half smile, real skin with pores and fine lines on the forehead, signature details that must stay: thin rectangular glasses, short black hair with a light fringe, a black suit over an open-collar white shirt, a slim black suit jacket with the sleeves pushed up, a white shirt with the collar open and no tie, black trousers, a black leather belt, large black headphones around his neck, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `xu_san_expr.png`
用途：徐三（DJ）第二步 表情四宫格：上传锁定的 xu_san_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/xu_san_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐三的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（戴着一边耳机，面无表情地跟着节奏点头），四格都是正面头肩，38 岁的中国男人，中等身材，神情沉稳，戴细框长方形眼镜；黑色短发，碎刘海垂在额前；胡子刮净有淡青色，嘴角半笑；皮肤有毛孔，额头细纹，招牌特征不能丢：细框长方形眼镜 + 黑色短发碎刘海 + 黑西装配敞领白衬衫，修身黑西装外套推着袖子，白衬衫敞领不打领带，黑西裤，脖子上挂一副黑色大耳机；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 38-year-old Chinese man, medium build, a calm oval face, thin rectangular glasses, short black hair with a light choppy fringe over the forehead, clean-shaven with a faint shadow, a composed half smile, real skin with pores and fine lines on the forehead, signature details that must stay: thin rectangular glasses, short black hair with a light fringe, a black suit over an open-collar white shirt, a slim black suit jacket with the sleeves pushed up, a white shirt with the collar open and no tie, black trousers, a black leather belt, large black headphones around his neck, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `xu_san_full.png`
用途：徐三（DJ）第二步 全身：上传锁定的 xu_san_face.png 生成

上传：图1 = `refs/xu_san_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是徐三的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，右手拿着银色有线话筒，话筒在嘴的斜下方，38 岁的中国男人，中等身材，神情沉稳，戴细框长方形眼镜；黑色短发，碎刘海垂在额前；胡子刮净有淡青色，嘴角半笑；皮肤有毛孔，额头细纹，招牌特征不能丢：细框长方形眼镜 + 黑色短发碎刘海 + 黑西装配敞领白衬衫，修身黑西装外套推着袖子，白衬衫敞领不打领带，黑西裤，脖子上挂一副黑色大耳机；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 38-year-old Chinese man, medium build, a calm oval face, thin rectangular glasses, short black hair with a light choppy fringe over the forehead, clean-shaven with a faint shadow, a composed half smile, real skin with pores and fine lines on the forehead, signature details that must stay: thin rectangular glasses, short black hair with a light fringe, a black suit over an open-collar white shirt, a slim black suit jacket with the sleeves pushed up, a white shirt with the collar open and no tie, black trousers, a black leather belt, large black headphones around his neck, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `xu_san_sheet.png`
用途：徐三（DJ）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含徐三的生成都上传，只认脸，不当画面）

拼图用：`xu_san_face.png`、`xu_san_34.png`、`xu_san_profile.png`、`xu_san_half.png`、`xu_san_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 冯宝宝（baobao）

原作图：`refs/canon/feng_baobao.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/42203)）

原作里的样子：官方图：黑色长直发很长，垂到腰下，有几缕碎刘海分在额前；面无表情，眼睛直直地看；浅灰色长袖衬衫扣到领口，衬衫下摆塞进深灰色长裙里，长裙到小腿，黑色平底鞋。

### 第一步 原作图 → 真人正面像

#### `baobao_face.png`
用途：冯宝宝（副歌）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/feng_baobao.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，看上去 25 岁的成年中国女人，瘦小，鹅蛋脸，表情放空、平静；大而黑的眼睛直直看着、很少眨；黑色长直发垂到腰下；上镜淡妆，唇色自然，皮肤有毛孔，招牌特征不能丢：垂到腰下的黑色长直发 + 面无表情 + 浅灰长袖衬衫配深灰长裙，浅灰色长袖衬衫扣到领口、塞进裙子，深灰色百褶长裙到小腿，黑色系带短靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a Chinese woman who looks 25, slim and small, an oval face with a completely blank calm expression, large dark steady eyes that barely blink, straight black eyebrows, very long straight black hair falling past the waist with a few loose strands parted over the forehead, light on-camera stage makeup with a natural lip, real skin with fine pores, signature details that must stay: very long straight black hair down past the waist, a completely blank expression, a light grey long-sleeve shirt with a long dark grey skirt, a light grey long-sleeve cotton shirt buttoned to the collar and tucked in, a long dark grey pleated skirt to the mid calf, a slim black leather belt, black lace-up combat boots, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `baobao_34.png`
用途：冯宝宝（副歌）第二步 四分之三侧面：上传锁定的 baobao_face.png 生成

上传：图1 = `refs/baobao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是冯宝宝的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，看上去 25 岁的成年中国女人，瘦小，鹅蛋脸，表情放空、平静；大而黑的眼睛直直看着、很少眨；黑色长直发垂到腰下；上镜淡妆，唇色自然，皮肤有毛孔，招牌特征不能丢：垂到腰下的黑色长直发 + 面无表情 + 浅灰长袖衬衫配深灰长裙，浅灰色长袖衬衫扣到领口、塞进裙子，深灰色百褶长裙到小腿，黑色系带短靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese woman who looks 25, slim and small, an oval face with a completely blank calm expression, large dark steady eyes that barely blink, straight black eyebrows, very long straight black hair falling past the waist with a few loose strands parted over the forehead, light on-camera stage makeup with a natural lip, real skin with fine pores, signature details that must stay: very long straight black hair down past the waist, a completely blank expression, a light grey long-sleeve shirt with a long dark grey skirt, a light grey long-sleeve cotton shirt buttoned to the collar and tucked in, a long dark grey pleated skirt to the mid calf, a slim black leather belt, black lace-up combat boots, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `baobao_profile.png`
用途：冯宝宝（副歌）第二步 正侧面：上传锁定的 baobao_face.png 生成

上传：图1 = `refs/baobao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是冯宝宝的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，看上去 25 岁的成年中国女人，瘦小，鹅蛋脸，表情放空、平静；大而黑的眼睛直直看着、很少眨；黑色长直发垂到腰下；上镜淡妆，唇色自然，皮肤有毛孔，招牌特征不能丢：垂到腰下的黑色长直发 + 面无表情 + 浅灰长袖衬衫配深灰长裙，浅灰色长袖衬衫扣到领口、塞进裙子，深灰色百褶长裙到小腿，黑色系带短靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese woman who looks 25, slim and small, an oval face with a completely blank calm expression, large dark steady eyes that barely blink, straight black eyebrows, very long straight black hair falling past the waist with a few loose strands parted over the forehead, light on-camera stage makeup with a natural lip, real skin with fine pores, signature details that must stay: very long straight black hair down past the waist, a completely blank expression, a light grey long-sleeve shirt with a long dark grey skirt, a light grey long-sleeve cotton shirt buttoned to the collar and tucked in, a long dark grey pleated skirt to the mid calf, a slim black leather belt, black lace-up combat boots, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `baobao_half.png`
用途：冯宝宝（副歌）第二步 半身：上传锁定的 baobao_face.png 生成

上传：图1 = `refs/baobao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是冯宝宝的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，右手拿着银色有线话筒，话筒在嘴的斜下方，看上去 25 岁的成年中国女人，瘦小，鹅蛋脸，表情放空、平静；大而黑的眼睛直直看着、很少眨；黑色长直发垂到腰下；上镜淡妆，唇色自然，皮肤有毛孔，招牌特征不能丢：垂到腰下的黑色长直发 + 面无表情 + 浅灰长袖衬衫配深灰长裙，浅灰色长袖衬衫扣到领口、塞进裙子，深灰色百褶长裙到小腿，黑色系带短靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese woman who looks 25, slim and small, an oval face with a completely blank calm expression, large dark steady eyes that barely blink, straight black eyebrows, very long straight black hair falling past the waist with a few loose strands parted over the forehead, light on-camera stage makeup with a natural lip, real skin with fine pores, signature details that must stay: very long straight black hair down past the waist, a completely blank expression, a light grey long-sleeve shirt with a long dark grey skirt, a light grey long-sleeve cotton shirt buttoned to the collar and tucked in, a long dark grey pleated skirt to the mid calf, a slim black leather belt, black lace-up combat boots, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `baobao_expr.png`
用途：冯宝宝（副歌）第二步 表情四宫格：上传锁定的 baobao_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/baobao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是冯宝宝的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（站在立麦前面无表情地看着台上，眨了一下眼），四格都是正面头肩，看上去 25 岁的成年中国女人，瘦小，鹅蛋脸，表情放空、平静；大而黑的眼睛直直看着、很少眨；黑色长直发垂到腰下；上镜淡妆，唇色自然，皮肤有毛孔，招牌特征不能丢：垂到腰下的黑色长直发 + 面无表情 + 浅灰长袖衬衫配深灰长裙，浅灰色长袖衬衫扣到领口、塞进裙子，深灰色百褶长裙到小腿，黑色系带短靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese woman who looks 25, slim and small, an oval face with a completely blank calm expression, large dark steady eyes that barely blink, straight black eyebrows, very long straight black hair falling past the waist with a few loose strands parted over the forehead, light on-camera stage makeup with a natural lip, real skin with fine pores, signature details that must stay: very long straight black hair down past the waist, a completely blank expression, a light grey long-sleeve shirt with a long dark grey skirt, a light grey long-sleeve cotton shirt buttoned to the collar and tucked in, a long dark grey pleated skirt to the mid calf, a slim black leather belt, black lace-up combat boots, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `baobao_full.png`
用途：冯宝宝（副歌）第二步 全身：上传锁定的 baobao_face.png 生成

上传：图1 = `refs/baobao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是冯宝宝的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，右手拿着银色有线话筒，话筒在嘴的斜下方，看上去 25 岁的成年中国女人，瘦小，鹅蛋脸，表情放空、平静；大而黑的眼睛直直看着、很少眨；黑色长直发垂到腰下；上镜淡妆，唇色自然，皮肤有毛孔，招牌特征不能丢：垂到腰下的黑色长直发 + 面无表情 + 浅灰长袖衬衫配深灰长裙，浅灰色长袖衬衫扣到领口、塞进裙子，深灰色百褶长裙到小腿，黑色系带短靴；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a Chinese woman who looks 25, slim and small, an oval face with a completely blank calm expression, large dark steady eyes that barely blink, straight black eyebrows, very long straight black hair falling past the waist with a few loose strands parted over the forehead, light on-camera stage makeup with a natural lip, real skin with fine pores, signature details that must stay: very long straight black hair down past the waist, a completely blank expression, a light grey long-sleeve shirt with a long dark grey skirt, a light grey long-sleeve cotton shirt buttoned to the collar and tucked in, a long dark grey pleated skirt to the mid calf, a slim black leather belt, black lace-up combat boots, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `baobao_sheet.png`
用途：冯宝宝（副歌）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含冯宝宝的生成都上传，只认脸，不当画面）

拼图用：`baobao_face.png`、`baobao_34.png`、`baobao_profile.png`、`baobao_half.png`、`baobao_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 张灵玉（lingyu）

原作图：`refs/canon/zhang_lingyu.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/42208)）

原作里的样子：官方图（黑白插画）：白色长发很长，披散飘起，刘海垂在脸前；闭着眼，神情冷静；身穿白色宽袖道袍和白色宽裤，布鞋；周围是大片黑色墨线一样的雷（阴五雷）。

### 第一步 原作图 → 真人正面像

#### `lingyu_face.png`
用途：张灵玉（副歌）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/zhang_lingyu.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，24 岁的中国男人，高，站得笔直，窄脸，颧骨高，表情严肃，深色眉毛平直，眼神沉静；白色长发过肩、上半部分往后束起；上镜淡妆，皮肤有毛孔，耳朵微红，招牌特征不能丢：白色长发 + 白色宽袖道袍，剪裁利落的白色宽袖交领长外套，白色高领打底，白色阔腿裤，黑布腰带，白布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 24-year-old Chinese man, tall and very upright, a narrow serious face with high cheekbones, cool straight dark eyebrows, calm reserved dark eyes, long white hair falling past the shoulders with the top half tied back and a few loose strands over the face, light on-camera stage makeup, real skin with fine pores and a slight flush on the ears, signature details that must stay: long white hair, a white wide-sleeved Taoist robe, a sharply cut white long coat with wide Taoist sleeves and a white crossed collar, a slim white high-neck inner top, white wide trousers, a black cloth sash, white cloth shoes, matte cotton and silk, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `lingyu_34.png`
用途：张灵玉（副歌）第二步 四分之三侧面：上传锁定的 lingyu_face.png 生成

上传：图1 = `refs/lingyu_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张灵玉的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，24 岁的中国男人，高，站得笔直，窄脸，颧骨高，表情严肃，深色眉毛平直，眼神沉静；白色长发过肩、上半部分往后束起；上镜淡妆，皮肤有毛孔，耳朵微红，招牌特征不能丢：白色长发 + 白色宽袖道袍，剪裁利落的白色宽袖交领长外套，白色高领打底，白色阔腿裤，黑布腰带，白布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, tall and very upright, a narrow serious face with high cheekbones, cool straight dark eyebrows, calm reserved dark eyes, long white hair falling past the shoulders with the top half tied back and a few loose strands over the face, light on-camera stage makeup, real skin with fine pores and a slight flush on the ears, signature details that must stay: long white hair, a white wide-sleeved Taoist robe, a sharply cut white long coat with wide Taoist sleeves and a white crossed collar, a slim white high-neck inner top, white wide trousers, a black cloth sash, white cloth shoes, matte cotton and silk, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `lingyu_profile.png`
用途：张灵玉（副歌）第二步 正侧面：上传锁定的 lingyu_face.png 生成

上传：图1 = `refs/lingyu_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张灵玉的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，24 岁的中国男人，高，站得笔直，窄脸，颧骨高，表情严肃，深色眉毛平直，眼神沉静；白色长发过肩、上半部分往后束起；上镜淡妆，皮肤有毛孔，耳朵微红，招牌特征不能丢：白色长发 + 白色宽袖道袍，剪裁利落的白色宽袖交领长外套，白色高领打底，白色阔腿裤，黑布腰带，白布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, tall and very upright, a narrow serious face with high cheekbones, cool straight dark eyebrows, calm reserved dark eyes, long white hair falling past the shoulders with the top half tied back and a few loose strands over the face, light on-camera stage makeup, real skin with fine pores and a slight flush on the ears, signature details that must stay: long white hair, a white wide-sleeved Taoist robe, a sharply cut white long coat with wide Taoist sleeves and a white crossed collar, a slim white high-neck inner top, white wide trousers, a black cloth sash, white cloth shoes, matte cotton and silk, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `lingyu_half.png`
用途：张灵玉（副歌）第二步 半身：上传锁定的 lingyu_face.png 生成

上传：图1 = `refs/lingyu_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张灵玉的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，右手拿着银色有线话筒，话筒在嘴的斜下方，24 岁的中国男人，高，站得笔直，窄脸，颧骨高，表情严肃，深色眉毛平直，眼神沉静；白色长发过肩、上半部分往后束起；上镜淡妆，皮肤有毛孔，耳朵微红，招牌特征不能丢：白色长发 + 白色宽袖道袍，剪裁利落的白色宽袖交领长外套，白色高领打底，白色阔腿裤，黑布腰带，白布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, tall and very upright, a narrow serious face with high cheekbones, cool straight dark eyebrows, calm reserved dark eyes, long white hair falling past the shoulders with the top half tied back and a few loose strands over the face, light on-camera stage makeup, real skin with fine pores and a slight flush on the ears, signature details that must stay: long white hair, a white wide-sleeved Taoist robe, a sharply cut white long coat with wide Taoist sleeves and a white crossed collar, a slim white high-neck inner top, white wide trousers, a black cloth sash, white cloth shoes, matte cotton and silk, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `lingyu_expr.png`
用途：张灵玉（副歌）第二步 表情四宫格：上传锁定的 lingyu_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/lingyu_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张灵玉的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（站在立麦前背挺得笔直，表情严肃，耳朵有点红），四格都是正面头肩，24 岁的中国男人，高，站得笔直，窄脸，颧骨高，表情严肃，深色眉毛平直，眼神沉静；白色长发过肩、上半部分往后束起；上镜淡妆，皮肤有毛孔，耳朵微红，招牌特征不能丢：白色长发 + 白色宽袖道袍，剪裁利落的白色宽袖交领长外套，白色高领打底，白色阔腿裤，黑布腰带，白布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, tall and very upright, a narrow serious face with high cheekbones, cool straight dark eyebrows, calm reserved dark eyes, long white hair falling past the shoulders with the top half tied back and a few loose strands over the face, light on-camera stage makeup, real skin with fine pores and a slight flush on the ears, signature details that must stay: long white hair, a white wide-sleeved Taoist robe, a sharply cut white long coat with wide Taoist sleeves and a white crossed collar, a slim white high-neck inner top, white wide trousers, a black cloth sash, white cloth shoes, matte cotton and silk, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `lingyu_full.png`
用途：张灵玉（副歌）第二步 全身：上传锁定的 lingyu_face.png 生成

上传：图1 = `refs/lingyu_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是张灵玉的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，右手拿着银色有线话筒，话筒在嘴的斜下方，24 岁的中国男人，高，站得笔直，窄脸，颧骨高，表情严肃，深色眉毛平直，眼神沉静；白色长发过肩、上半部分往后束起；上镜淡妆，皮肤有毛孔，耳朵微红，招牌特征不能丢：白色长发 + 白色宽袖道袍，剪裁利落的白色宽袖交领长外套，白色高领打底，白色阔腿裤，黑布腰带，白布鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, holding a silver corded microphone below the mouth, the same person as the omni reference, same face, hairstyle and hair colour, a 24-year-old Chinese man, tall and very upright, a narrow serious face with high cheekbones, cool straight dark eyebrows, calm reserved dark eyes, long white hair falling past the shoulders with the top half tied back and a few loose strands over the face, light on-camera stage makeup, real skin with fine pores and a slight flush on the ears, signature details that must stay: long white hair, a white wide-sleeved Taoist robe, a sharply cut white long coat with wide Taoist sleeves and a white crossed collar, a slim white high-neck inner top, white wide trousers, a black cloth sash, white cloth shoes, matte cotton and silk, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `lingyu_sheet.png`
用途：张灵玉（副歌）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含张灵玉的生成都上传，只认脸，不当画面）

拼图用：`lingyu_face.png`、`lingyu_34.png`、`lingyu_profile.png`、`lingyu_half.png`、`lingyu_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 风莎燕（shayan）

原作图：`refs/canon/feng_shayan.jpg`（来源：[Bangumi 角色页](https://bgm.tv/character/42213)）

原作里的样子：官方图：银白偏淡紫色的层次短发，长度到下巴，发梢被风吹乱；淡紫色眼睛，眼尾上挑，笑得自信又挑衅；白色挂脖露背上衣，领口是一圈白色立领。身高 171cm。

### 第一步 原作图 → 真人正面像

#### `shayan_face.png`
用途：风莎燕（客串）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：图1 = `refs/canon/feng_shayan.jpg`（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片）

即梦 CN：
```
把图1里的动漫角色拍成真人综艺定妆照（原作图：只参考发色、发型、眼睛和服装配色，不照抄画风，变成真人照片），正面头肩像，正对镜头，眼睛平视，22 岁的成年中国女人，身高 171 厘米，体格匀称有力，心形脸；眼尾上挑，淡紫色眼睛，笑得自信带点挑衅；银白偏淡紫的层次短发，长度到下巴；上镜淡妆，皮肤有毛孔，招牌特征不能丢：银白偏淡紫的层次短发 + 淡紫色眼睛 + 白色挂脖上衣，白色缎面挂脖露背上衣，肩披淡紫灰短西装，白色高腰阔腿裤，白色短靴，小银圈耳环；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，是真实拍摄的照片，不是画，无文字、无水印、无标志。
```
Midjourney EN：
```
<原作图链接> front head-and-shoulders portrait facing the camera straight on, eyes level, photoreal live-action costume test photo of the character in the image prompt, only the hair colour, hairstyle, eyes and costume palette are taken from it, not the drawing style, a 22-year-old Chinese woman, 171 cm and athletic, a heart-shaped face, sharp lively upturned eyes with pale violet irises, a confident challenging smile and a slight tilt of the chin, silver-white chin-length layered hair with a faint lilac tint and wind-tousled tips, light on-camera stage makeup with defined brows, real skin with fine pores, signature details that must stay: silver-white short layered hair with a faint lilac tint, pale violet eyes, a white halter-neck top, a white satin halter-neck top with a small stand collar and an open back, a cropped lilac-grey tailored jacket worn over the shoulders, high-waisted white tailored wide trousers, white pointed ankle boots, small silver hoop earrings, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, a real photograph, no text, no letters, no logos --iw 1.5 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `shayan_34.png`
用途：风莎燕（客串）第二步 四分之三侧面：上传锁定的 shayan_face.png 生成

上传：图1 = `refs/shayan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风莎燕的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，22 岁的成年中国女人，身高 171 厘米，体格匀称有力，心形脸；眼尾上挑，淡紫色眼睛，笑得自信带点挑衅；银白偏淡紫的层次短发，长度到下巴；上镜淡妆，皮肤有毛孔，招牌特征不能丢：银白偏淡紫的层次短发 + 淡紫色眼睛 + 白色挂脖上衣，白色缎面挂脖露背上衣，肩披淡紫灰短西装，白色高腰阔腿裤，白色短靴，小银圈耳环；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 22-year-old Chinese woman, 171 cm and athletic, a heart-shaped face, sharp lively upturned eyes with pale violet irises, a confident challenging smile and a slight tilt of the chin, silver-white chin-length layered hair with a faint lilac tint and wind-tousled tips, light on-camera stage makeup with defined brows, real skin with fine pores, signature details that must stay: silver-white short layered hair with a faint lilac tint, pale violet eyes, a white halter-neck top, a white satin halter-neck top with a small stand collar and an open back, a cropped lilac-grey tailored jacket worn over the shoulders, high-waisted white tailored wide trousers, white pointed ankle boots, small silver hoop earrings, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `shayan_profile.png`
用途：风莎燕（客串）第二步 正侧面：上传锁定的 shayan_face.png 生成

上传：图1 = `refs/shayan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风莎燕的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，22 岁的成年中国女人，身高 171 厘米，体格匀称有力，心形脸；眼尾上挑，淡紫色眼睛，笑得自信带点挑衅；银白偏淡紫的层次短发，长度到下巴；上镜淡妆，皮肤有毛孔，招牌特征不能丢：银白偏淡紫的层次短发 + 淡紫色眼睛 + 白色挂脖上衣，白色缎面挂脖露背上衣，肩披淡紫灰短西装，白色高腰阔腿裤，白色短靴，小银圈耳环；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 22-year-old Chinese woman, 171 cm and athletic, a heart-shaped face, sharp lively upturned eyes with pale violet irises, a confident challenging smile and a slight tilt of the chin, silver-white chin-length layered hair with a faint lilac tint and wind-tousled tips, light on-camera stage makeup with defined brows, real skin with fine pores, signature details that must stay: silver-white short layered hair with a faint lilac tint, pale violet eyes, a white halter-neck top, a white satin halter-neck top with a small stand collar and an open back, a cropped lilac-grey tailored jacket worn over the shoulders, high-waisted white tailored wide trousers, white pointed ankle boots, small silver hoop earrings, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `shayan_half.png`
用途：风莎燕（客串）第二步 半身：上传锁定的 shayan_face.png 生成

上传：图1 = `refs/shayan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风莎燕的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，22 岁的成年中国女人，身高 171 厘米，体格匀称有力，心形脸；眼尾上挑，淡紫色眼睛，笑得自信带点挑衅；银白偏淡紫的层次短发，长度到下巴；上镜淡妆，皮肤有毛孔，招牌特征不能丢：银白偏淡紫的层次短发 + 淡紫色眼睛 + 白色挂脖上衣，白色缎面挂脖露背上衣，肩披淡紫灰短西装，白色高腰阔腿裤，白色短靴，小银圈耳环；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a 22-year-old Chinese woman, 171 cm and athletic, a heart-shaped face, sharp lively upturned eyes with pale violet irises, a confident challenging smile and a slight tilt of the chin, silver-white chin-length layered hair with a faint lilac tint and wind-tousled tips, light on-camera stage makeup with defined brows, real skin with fine pores, signature details that must stay: silver-white short layered hair with a faint lilac tint, pale violet eyes, a white halter-neck top, a white satin halter-neck top with a small stand collar and an open back, a cropped lilac-grey tailored jacket worn over the shoulders, high-waisted white tailored wide trousers, white pointed ankle boots, small silver hoop earrings, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `shayan_expr.png`
用途：风莎燕（客串）第二步 表情四宫格：上传锁定的 shayan_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/shayan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风莎燕的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（坐在观众席里翻了个白眼，又忍不住笑出来，赶紧捂住嘴），四格都是正面头肩，22 岁的成年中国女人，身高 171 厘米，体格匀称有力，心形脸；眼尾上挑，淡紫色眼睛，笑得自信带点挑衅；银白偏淡紫的层次短发，长度到下巴；上镜淡妆，皮肤有毛孔，招牌特征不能丢：银白偏淡紫的层次短发 + 淡紫色眼睛 + 白色挂脖上衣，白色缎面挂脖露背上衣，肩披淡紫灰短西装，白色高腰阔腿裤，白色短靴，小银圈耳环；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 22-year-old Chinese woman, 171 cm and athletic, a heart-shaped face, sharp lively upturned eyes with pale violet irises, a confident challenging smile and a slight tilt of the chin, silver-white chin-length layered hair with a faint lilac tint and wind-tousled tips, light on-camera stage makeup with defined brows, real skin with fine pores, signature details that must stay: silver-white short layered hair with a faint lilac tint, pale violet eyes, a white halter-neck top, a white satin halter-neck top with a small stand collar and an open back, a cropped lilac-grey tailored jacket worn over the shoulders, high-waisted white tailored wide trousers, white pointed ankle boots, small silver hoop earrings, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `shayan_full.png`
用途：风莎燕（客串）第二步 全身：上传锁定的 shayan_face.png 生成

上传：图1 = `refs/shayan_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是风莎燕的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，22 岁的成年中国女人，身高 171 厘米，体格匀称有力，心形脸；眼尾上挑，淡紫色眼睛，笑得自信带点挑衅；银白偏淡紫的层次短发，长度到下巴；上镜淡妆，皮肤有毛孔，招牌特征不能丢：银白偏淡紫的层次短发 + 淡紫色眼睛 + 白色挂脖上衣，白色缎面挂脖露背上衣，肩披淡紫灰短西装，白色高腰阔腿裤，白色短靴，小银圈耳环；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a 22-year-old Chinese woman, 171 cm and athletic, a heart-shaped face, sharp lively upturned eyes with pale violet irises, a confident challenging smile and a slight tilt of the chin, silver-white chin-length layered hair with a faint lilac tint and wind-tousled tips, light on-camera stage makeup with defined brows, real skin with fine pores, signature details that must stay: silver-white short layered hair with a faint lilac tint, pale violet eyes, a white halter-neck top, a white satin halter-neck top with a small stand collar and an open back, a cropped lilac-grey tailored jacket worn over the shoulders, high-waisted white tailored wide trousers, white pointed ankle boots, small silver hoop earrings, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `shayan_sheet.png`
用途：风莎燕（客串）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含风莎燕的生成都上传，只认脸，不当画面）

拼图用：`shayan_face.png`、`shayan_34.png`、`shayan_profile.png`、`shayan_half.png`、`shayan_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 诸葛家长辈（zhanglao）

原创角色，无原作图：第一步用文生图。

### 第一步 原作图 → 真人正面像

#### `zhanglao_face.png`
用途：诸葛家长辈（客串）第一步 定妆正面像：挑一张锁定，第二步每张图都上传它

上传：不上传图（文生图）

即梦 CN：
```
诸葛家长辈的真人综艺定妆照（原创角色，没有原作图，直接文生图），正面头肩像，正对镜头，眼睛平视，62 岁的中国男人，瘦，长脸，神情端正；灰色山羊短胡和细八字胡；深藏青带银丝的头发整齐往后梳；嘴唇抿紧，一脸骄傲；皮肤有皱纹，太阳穴有老年斑，白色立领衬衫，藏青色背带，深藏青修身长外套（袖口细八卦线），藏青西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
front head-and-shoulders portrait facing the camera straight on, eyes level, a 62-year-old Chinese man, thin, a long dignified face, a short grey goatee and a thin grey moustache, dark navy-grey hair streaked with silver and combed neatly back, tight proud lips, real skin with wrinkles and age spots on the temples, a white band-collar shirt, navy suspenders, a long dark navy tailored coat with a thin bagua line embroidered on the cuffs, navy trousers, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```

### 第二步 用正面像生成其他角度

#### `zhanglao_34.png`
用途：诸葛家长辈（客串）第二步 四分之三侧面：上传锁定的 zhanglao_face.png 生成

上传：图1 = `refs/zhanglao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家长辈的定妆正面像：保持同一张脸、发型和发色，拍同一个人的四分之三侧面头肩像，身体和脸微微朝左，62 岁的中国男人，瘦，长脸，神情端正；灰色山羊短胡和细八字胡；深藏青带银丝的头发整齐往后梳；嘴唇抿紧，一脸骄傲；皮肤有皱纹，太阳穴有老年斑，白色立领衬衫，藏青色背带，深藏青修身长外套（袖口细八卦线），藏青西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
three-quarter head-and-shoulders view turned slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 62-year-old Chinese man, thin, a long dignified face, a short grey goatee and a thin grey moustache, dark navy-grey hair streaked with silver and combed neatly back, tight proud lips, real skin with wrinkles and age spots on the temples, a white band-collar shirt, navy suspenders, a long dark navy tailored coat with a thin bagua line embroidered on the cuffs, navy trousers, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `zhanglao_profile.png`
用途：诸葛家长辈（客串）第二步 正侧面：上传锁定的 zhanglao_face.png 生成

上传：图1 = `refs/zhanglao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家长辈的定妆正面像：保持同一张脸、发型和发色，拍同一个人的正侧面头肩像，脸微微朝左，看得清侧脸轮廓和发型，62 岁的中国男人，瘦，长脸，神情端正；灰色山羊短胡和细八字胡；深藏青带银丝的头发整齐往后梳；嘴唇抿紧，一脸骄傲；皮肤有皱纹，太阳穴有老年斑，白色立领衬衫，藏青色背带，深藏青修身长外套（袖口细八卦线），藏青西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
strict profile head-and-shoulders view facing slightly to the left, the same person as the omni reference, same face, hairstyle and hair colour, a 62-year-old Chinese man, thin, a long dignified face, a short grey goatee and a thin grey moustache, dark navy-grey hair streaked with silver and combed neatly back, tight proud lips, real skin with wrinkles and age spots on the temples, a white band-collar shirt, navy suspenders, a long dark navy tailored coat with a thin bagua line embroidered on the cuffs, navy trousers, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `zhanglao_half.png`
用途：诸葛家长辈（客串）第二步 半身：上传锁定的 zhanglao_face.png 生成

上传：图1 = `refs/zhanglao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家长辈的定妆正面像：保持同一张脸、发型和发色，拍同一个人的腰以上半身照，身体微微微微朝左，穿全套舞台服装，62 岁的中国男人，瘦，长脸，神情端正；灰色山羊短胡和细八字胡；深藏青带银丝的头发整齐往后梳；嘴唇抿紧，一脸骄傲；皮肤有皱纹，太阳穴有老年斑，白色立领衬衫，藏青色背带，深藏青修身长外套（袖口细八卦线），藏青西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
waist-up shot turned slightly slightly to the left in the full stage wardrobe, the same person as the omni reference, same face, hairstyle and hair colour, a 62-year-old Chinese man, thin, a long dignified face, a short grey goatee and a thin grey moustache, dark navy-grey hair streaked with silver and combed neatly back, tight proud lips, real skin with wrinkles and age spots on the temples, a white band-collar shirt, navy suspenders, a long dark navy tailored coat with a thin bagua line embroidered on the cuffs, navy trousers, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 3:4 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `zhanglao_expr.png`
用途：诸葛家长辈（客串）第二步 表情四宫格：上传锁定的 zhanglao_face.png 生成（可选：只用来试表情、挑招牌表情，不拼进组图，视频单元不用）

上传：图1 = `refs/zhanglao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家长辈的定妆正面像：保持同一张脸、发型和发色，拍同一个人的同一个人的表情四宫格，2x2 拼在一张图里：笑、认真、惊讶、招牌表情（坐在观众席里双手拄着手杖，嘴唇抿紧，下巴微微抬起，眼神里全是期望），四格都是正面头肩，62 岁的中国男人，瘦，长脸，神情端正；灰色山羊短胡和细八字胡；深藏青带银丝的头发整齐往后梳；嘴唇抿紧，一脸骄傲；皮肤有皱纹，太阳穴有老年斑，白色立领衬衫，藏青色背带，深藏青修身长外套（袖口细八卦线），藏青西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
a 2x2 expression grid of the same person, four front head-and-shoulders frames: laughing, serious, surprised, and the character's signature reaction face, the same person as the omni reference, same face, hairstyle and hair colour, a 62-year-old Chinese man, thin, a long dignified face, a short grey goatee and a thin grey moustache, dark navy-grey hair streaked with silver and combed neatly back, tight proud lips, real skin with wrinkles and age spots on the temples, a white band-collar shirt, navy suspenders, a long dark navy tailored coat with a thin bagua line embroidered on the cuffs, navy trousers, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 1:1 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

#### `zhanglao_full.png`
用途：诸葛家长辈（客串）第二步 全身：上传锁定的 zhanglao_face.png 生成

上传：图1 = `refs/zhanglao_face.png`（定妆正面像：保持同一张脸、发型和发色）

即梦 CN：
```
图1是诸葛家长辈的定妆正面像：保持同一张脸、发型和发色，拍同一个人的全身照，从头到鞋都在画面里，站姿自然，身体微微朝左，穿全套舞台服装和鞋，62 岁的中国男人，瘦，长脸，神情端正；灰色山羊短胡和细八字胡；深藏青带银丝的头发整齐往后梳；嘴唇抿紧，一脸骄傲；皮肤有皱纹，太阳穴有老年斑，白色立领衬衫，藏青色背带，深藏青修身长外套（袖口细八卦线），藏青西裤，黑皮鞋；衣服上没有文字，动漫角色真人化上综艺：保留原作的发色、发型、眼睛颜色和招牌物件，服装改成当代街头潮牌和舞台演出服，配色沿用原作，可以加耳钉、细项链这类小配饰；成年人的身材比例；上镜的舞台妆：眉形清楚、眼妆干净、嘴唇有自然光泽，头发做过造型、发丝有层次；皮肤是真实的，有细小毛孔；原创面孔，不像任何真实的明星或演员，也不照搬任何已有 AI 节目里的角色脸，综艺节目定妆照的拍摄现场：深炭灰色无缝背景布，柔和的棚拍光，无文字、无水印、无标志。
```
Midjourney EN：
```
full-body shot head to shoes, natural stance turned slightly to the left, full stage costume and shoes, the same person as the omni reference, same face, hairstyle and hair colour, a 62-year-old Chinese man, thin, a long dignified face, a short grey goatee and a thin grey moustache, dark navy-grey hair streaked with silver and combed neatly back, tight proud lips, real skin with wrinkles and age spots on the temples, a white band-collar shirt, navy suspenders, a long dark navy tailored coat with a thin bagua line embroidered on the cuffs, navy trousers, black leather shoes, no lettering, live-action version of an anime character appearing on a TV rap show: canon hair colour, hairstyle and eye colour kept together with the signature items, costume translated into contemporary streetwear and stage wear in the canon palette, small earrings or a thin chain allowed, adult proportions, polished on-camera stage makeup with defined brows, clean eye makeup and a natural sheen on the lips, styled layered hair, real skin with fine pores, an original face that does not resemble any real celebrity or actor and copies no existing AI show character, TV-show costume test photo on a dark charcoal seamless backdrop, soft studio light, no text, no letters, no logos --oref <定妆正面像链接> --ow 100 --ar 2:3 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
Midjourney V6 没有 --oref，用 --cref <定妆正面像链接> --cw 100 代替。

### 第三步 锁定并拼成定妆组图

#### `zhanglao_sheet.png`
用途：诸葛家长辈（客串）第三步 定妆组图：由 aigc-mv ep sheets 把锁定的 face/34/profile/half/full 拼成，视频单元只传这一张（所有含诸葛家长辈的生成都上传，只认脸，不当画面）

拼图用：`zhanglao_face.png`、`zhanglao_34.png`、`zhanglao_profile.png`、`zhanglao_half.png`、`zhanglao_full.png`（`aigc-mv ep sheets` 自动拼，不用提示词）

## 场景图 / 背景板

观众席要坐满人，所以场景图要做。即梦按上传的图来认场馆：只传一张空场馆，生成出来的看台常常是空的或者稀稀拉拉，每个镜头的场馆样子也会不一样。所以给场馆的每个机位各做一张锁定的背景板，一共 9 张；每个镜头按它的调度自动配一张（分镜表的「场景图」列），视频单元上传它。这些图是原创的场景照片，不来自任何官方图，可以放心上传。

### 做哪些、不做哪些

| 场景图 | 用途 | 观众 | 用在镜头 | 用在单元（实际上传） |
| --- | --- | --- | --- | --- |
| `venue.png` | 主场景：选手、队友、对峙、双人镜头的背景（先做这张，锁定后其他场景图都参考它） | 坐满，看得清脸 | s005、s006、s007、s008、s010、s012、s013、s014 等 44 个 | u04、u05、u06、u07、u09、u11、u12、u13、u14、u15、u16、u18、u19、u20、u21、u22、u23、u24、u25、u26、u27、u28、u33、u39、u43、u44 |
| `venue_high.png` | 开场和片尾的高位全景（摇臂镜头的起幅和落幅） | 坐满，看得清脸 | s001、s065、s069 | u01、u37、u41 |
| `venue_dark.png` | 揭晓前的灭灯：背影追光、空舞台、低头特写和追光特写的背景 | 灭灯，只有剪影 | s055、s056、s057、s058 | u29、u30、u31 |
| `crowd.png` | 观众欢呼的空镜（开场、间奏、片尾的观众镜头） | 坐满，看得清脸 | s063、s064、s068 | u35、u36、u40 |
| `crowd_reverse.png` | 反打：选手在台上把话筒伸向观众时，从台上往外看满场看台 | 坐满，看得清脸 | s062 | u34 |
| `cameo_seats.png` | 客串角色坐在观众席里的反应镜头（客串不画进这张图，座位留空） | 坐满，看得清脸 | s022、s024、s035 | u14、u15、u20 |
| `judges.png` | 评委反应镜头的背景 | 坐满，虚成光斑 | s020、s031、s044、s052 | u18、u24、u27 |
| `dj_booth.png` | 主持和 DJ 镜头的背景 | 坐满，虚成光斑 | s002、s003、s004、s066、s070 | u02、u03、u38、u42 |
| `hook_mics.png` | 副歌歌手在立麦前唱的背景（舞台后方的两支立麦） | 坐满，虚成光斑 | s009、s011、s028、s059、s061 | u08、u10、u17、u32、u33 |

不单独做的：地面八卦图案和 LED 大屏的特写图（分镜里没有这两种插入镜头，它们已经在舞台正面、高位全景和 DJ 台三张里）；每位评委、每位客串各一张座位图（一张评委席、一张前两排座位就够，人物靠定妆图放进去）；白天、彩排、后台这类场景（这一期全在晚上的直播现场）。

### 怎么做

1. 先做 `venue.png`（文生图），每张出 2 到 4 张候选，挑一张锁定。锁定以后不再改，改了就要重新生成所有用到它的镜头。
2. 其他场景图都上传一张已经锁定的场景图当图1（每张下面的「上传」写了是哪张），这样灯光、配色、地面图案和看台样式能对上。Midjourney 里把那张锁定图当 `--sref <场景图链接>`；这是自己生成的图，不是官方图，传上去没问题。
3. 挑图标准：看台是满的，没有空座位；观众是长相各不相同的普通成年人，不是动漫脸、不像任何真实名人；画面里没有任何文字和标志（节目 logo 是剪辑时叠上去的角标）；和上一张锁定图放在一起像同一个场馆。

### 观众密度：图里坐满，提示词里再说一遍

两层都做：场景图本身就是满场（「看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样」），视频模型照着图生成时看台不会空；每个单元的提示词里还有一行【观众】，点名哪几个镜头能看到观众席，再写一次坐满、不要空座位、不要空看台。灭灯那几个镜头例外：观众席是黑的，只有剪影和零星的荧光棒，提示词也写明不要把观众照亮。

### 客串角色坐哪儿

客串角色不画进任何场景图。`cameo_seats.png` 把他们的座位留空：风莎燕坐在观众席第二排靠中间偏左；诸葛家长辈坐在观众席第一排正中。客串的反应镜头上传这个人的定妆组图和 `cameo_seats.png`，提示词写明坐在哪个座位（就是图里留空的那个），左右和身后是不认识的普通观众。同一个人的所有镜头用同一张图、同一句座位描述，所以位置不会跳。观众全景里不要求看到客串角色。

### 视频单元怎么上传

每个单元最多上传 9 张图（即梦 Seedance 2.0 全能参考的图片上限）：先放人物，每人只传一张定妆组图（最多 6 人），再放场景图，最多 2 张。一个单元里调度多于两种场景时，灭灯和客串座位这两张一定保留，其余按镜头时长选；超过上限时先去掉背景里虚化的队友，再去掉多出来的场景图。提示词的每个镜头都写了「背景照 @图片N」。

### 费用估算（没有生成任何图）

按 OpenRouter `openai/gpt-image-2.5-sunburst`、quality high、16:9 估算。账本里已经做过的 3:4 高质量图（带一张参考图）实际每张 $0.055 到 $0.060；16:9 是 1536x1024，和 3:4 的 1024x1536 像素一样多，所以按每张 $0.06 算，保守上限按每张 $0.12（两倍，留给更长的提示词、多一张参考图或者调价）。每张场景图做 4 张候选。

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

### `venue.png`
用途：主场景：选手、队友、对峙、双人镜头的背景（先做这张，锁定后其他场景图都参考它）

机位：全景，35mm 镜头，纪实感，人物和环境都看得清；从观众席正前方平视舞台，正面对称，地平线水平，台上没有人

用在镜头：s005、s006、s007、s008、s010、s012、s013、s014、s015、s016、s017、s018、s019、s021、s023、s025、s026、s027、s029、s030、s032、s033、s034、s036、s037、s038、s039、s040、s041、s042、s043、s045、s046、s047、s048、s049、s050、s051、s053、s054、s060、s067、s071、s072

用在单元：u04、u05、u06、u07、u09、u11、u12、u13、u14、u15、u16、u18、u19、u20、u21、u22、u23、u24、u25、u26、u27、u28、u33、u39、u43、u44

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

### `venue_high.png`
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

### `venue_dark.png`
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

### `crowd.png`
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

### `crowd_reverse.png`
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

### `cameo_seats.png`
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

### `judges.png`
用途：评委反应镜头的背景

机位：中景，腰以上，50mm 标准镜头；评委席的正面中景，座位上没有人

用在镜头：s020、s031、s044、s052

用在单元：u18、u24、u27

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

### `dj_booth.png`
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

### `hook_mics.png`
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

## 首帧和其他场景

### `plate_u01.png`
用途：u01 首帧（s01_cold_open · establish）

上传：图1 = `refs/venue_high.png`（场景图：保持同一个场馆、灯光、配色和观众席）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, 场馆高位全景，黑色擂台上的太极八卦图案一圈圈亮起来，红色灯带依次点亮，远处是夜里的龙虎山; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue_high.png（场馆高位全景）：保持同一个场馆、同样的灯光、配色和观众席，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，场馆高位全景，黑色擂台上的太极八卦图案一圈圈亮起来，红色灯带依次点亮，远处是夜里的龙虎山，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue_high.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u04.png`
用途：u04 首帧（s03_entrance · entrance）

上传：图1 = `refs/venue.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/a_sheet.png`（诸葛青的锁定定妆组图）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, a slim Chinese man of 24 with dark navy-blue side-fringed hair and eyes narrowed into a smile, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, 分屏：左右两队各三人并排走进场馆，选手走在最前面，队友跟在身后; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue.png（舞台正面）：保持同一个场馆、同样的灯光、配色和观众席，图2是诸葛青的锁定定妆组图：只认脸、发型和服装，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，右手始终握着一支银色有线话筒，话筒线垂下来，分屏：左右两队各三人并排走进场馆，选手走在最前面，队友跟在身后，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u05.png`
用途：u05 首帧（s03_entrance · entrance）

上传：图1 = `refs/venue.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/a_sheet.png`（诸葛青的锁定定妆组图）

Midjourney EN：
```
close-up, 135mm telephoto, compressed space, crowd and lights melted into large bokeh, broadcast long-lens camera, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, 诸葛青站定，盯着对面，身后的队友抱着手臂; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue.png（舞台正面）：保持同一个场馆、同样的灯光、配色和观众席，图2是诸葛青的锁定定妆组图：只认脸、发型和服装，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，特写，头和肩膀，135mm 长焦镜头，空间被压缩，背景的观众和灯虚成大片光斑，像综艺直播的长焦机位，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，右手始终握着一支银色有线话筒，话筒线垂下来，诸葛青站定，盯着对面，身后的队友抱着手臂，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u06.png`
用途：u06 首帧（s03_entrance · entrance）

上传：图1 = `refs/venue.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/b_sheet.png`（王也的锁定定妆组图）

Midjourney EN：
```
close-up, 135mm telephoto, compressed space, crowd and lights melted into large bokeh, broadcast long-lens camera, a 25-year-old Chinese man, tall with relaxed slightly slouched shoulders, a long face with a straight nose, lazy half-lidded dark eyes and low relaxed eyebrows, black hair pulled up into a round topknot at the back of the crown with several long loose strands falling over the forehead and framing the face, clean-shaven, light on-camera stage makeup, real skin with fine pores and faint tired shadows under the eyes, an oversized dark navy work jacket cut with a Taoist crossed collar, worn loose and slightly off the shoulders over a plain white T-shirt, loose dark navy pleated wide trousers, black canvas high-top shoes, a dark wooden bead bracelet, plain fabric with no lettering, 王也站定，盯着对面，身后的队友抱着手臂; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue.png（舞台正面）：保持同一个场馆、同样的灯光、配色和观众席，图2是王也的锁定定妆组图：只认脸、发型和服装，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，特写，头和肩膀，135mm 长焦镜头，空间被压缩，背景的观众和灯虚成大片光斑，像综艺直播的长焦机位，25 岁的中国男人，高个，肩膀松垮微驼；长脸，鼻梁直，眼皮半耷拉着、眼神懒散；黑发在头顶后方挽成圆发髻，几缕长碎发垂在脸边；胡子刮净，上镜淡妆，皮肤有毛孔，眼下有倦色，宽大的深藏青色交领工装外套松松披着，白色素T恤，深藏青色打褶阔腿裤，黑色高帮帆布鞋，深色木珠手串；衣服上没有文字，右手始终握着一支银色有线话筒，话筒线垂下来，王也站定，盯着对面，身后的队友抱着手臂，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u29.png`
用途：u29 首帧（s09_reveal · blackout）

上传：图1 = `refs/venue_dark.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/b_sheet.png`（王也的锁定定妆组图）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, a tall relaxed Chinese man of 25 with lazy half-lidded eyes and a black topknot with loose strands framing his face, an oversized dark navy work jacket cut with a Taoist crossed collar, worn loose and slightly off the shoulders over a plain white T-shirt, loose dark navy pleated wide trousers, black canvas high-top shoes, a dark wooden bead bracelet, plain fabric with no lettering, 全场灯灭，只剩头顶一束追光打在唱的人身上，从背后拍，只看得到背影剪影; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue_dark.png（灭灯舞台）：保持同一个场馆、同样的灯光、配色和观众席，图2是王也的锁定定妆组图：只认脸、发型和服装，观众席一片黑，只看得到前几排观众的黑色剪影和零星的红色荧光棒光点，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，25 岁的中国男人，高个，肩膀松垮微驼；长脸，鼻梁直，眼皮半耷拉着、眼神懒散；黑发在头顶后方挽成圆发髻，几缕长碎发垂在脸边；胡子刮净，上镜淡妆，皮肤有毛孔，眼下有倦色，宽大的深藏青色交领工装外套松松披着，白色素T恤，深藏青色打褶阔腿裤，黑色高帮帆布鞋，深色木珠手串；衣服上没有文字，右手始终握着一支银色有线话筒，话筒线垂下来，全场灯灭，只剩头顶一束追光打在唱的人身上，从背后拍，只看得到背影剪影，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue_dark.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u30.png`
用途：u30 首帧（s09_reveal · blackout）

上传：图1 = `refs/venue_dark.png`（场景图：保持同一个场馆、灯光、配色和观众席）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, 灭灯后的空舞台，只有追光落在地板的八卦图案上，观众席一片黑; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue_dark.png（灭灯舞台）：保持同一个场馆、同样的灯光、配色和观众席，观众席一片黑，只看得到前几排观众的黑色剪影和零星的红色荧光棒光点，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，灭灯后的空舞台，只有追光落在地板的八卦图案上，观众席一片黑，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue_dark.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u35.png`
用途：u35 首帧（s11_outro · crowd）

上传：图1 = `refs/crowd.png`（场景图：保持同一个场馆、灯光、配色和观众席）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, 看台上层层叠叠坐满了观众，挥着红色荧光棒，跟着一起喊; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 crowd.png（观众席中景）：保持同一个场馆、同样的灯光、配色和观众席，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，看台上层层叠叠坐满了观众，挥着红色荧光棒，跟着一起喊，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 crowd.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u36.png`
用途：u36 首帧（s11_outro · crowd）

上传：图1 = `refs/crowd.png`（场景图：保持同一个场馆、灯光、配色和观众席）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, 看台上层层叠叠坐满了观众，挥着红色荧光棒，挥手欢呼; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 crowd.png（观众席中景）：保持同一个场馆、同样的灯光、配色和观众席，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，看台上层层叠叠坐满了观众，挥着红色荧光棒，挥手欢呼，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 crowd.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u37.png`
用途：u37 首帧（s11_outro · establish）

上传：图1 = `refs/venue_high.png`（场景图：保持同一个场馆、灯光、配色和观众席）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, 场馆高位全景，全场观众站起来挥手，台上两队站在八卦图案两边; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue_high.png（场馆高位全景）：保持同一个场馆、同样的灯光、配色和观众席，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，场馆高位全景，全场观众站起来挥手，台上两队站在八卦图案两边，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue_high.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u38.png`
用途：u38 首帧（s11_outro · host）

上传：图1 = `refs/dj_booth.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/xu_san_sheet.png`（徐三的锁定定妆组图）

Midjourney EN：
```
close-up, 135mm telephoto, compressed space, crowd and lights melted into large bokeh, broadcast long-lens camera, a 38-year-old Chinese man, medium build, a calm oval face, thin rectangular glasses, short black hair with a light choppy fringe over the forehead, clean-shaven with a faint shadow, a composed half smile, real skin with pores and fine lines on the forehead, a slim black suit jacket with the sleeves pushed up, a white shirt with the collar open and no tie, black trousers, a black leather belt, large black headphones around his neck, no lettering, DJ 双手举过头顶，跟着观众一起喊; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 dj_booth.png（DJ 台）：保持同一个场馆、同样的灯光、配色和观众席，图2是徐三的锁定定妆组图：只认脸、发型和服装，特写，头和肩膀，135mm 长焦镜头，空间被压缩，背景的观众和灯虚成大片光斑，像综艺直播的长焦机位，38 岁的中国男人，中等身材，神情沉稳，戴细框长方形眼镜；黑色短发，碎刘海垂在额前；胡子刮净有淡青色，嘴角半笑；皮肤有毛孔，额头细纹，修身黑西装外套推着袖子，白衬衫敞领不打领带，黑西裤，脖子上挂一副黑色大耳机；衣服上没有文字，站在DJ台后面，一只手搭在唱盘上，DJ 双手举过头顶，跟着观众一起喊，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 dj_booth.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u39.png`
用途：u39 首帧（s11_outro · outro）

上传：图1 = `refs/venue.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/a_sheet.png`（诸葛青的锁定定妆组图）

Midjourney EN：
```
two-shot, 50mm lens, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, 两位选手放下话筒，隔着舞台互相看着，嘴角都挑了一下，嘴闭着; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue.png（舞台正面）：保持同一个场馆、同样的灯光、配色和观众席，图2是诸葛青的锁定定妆组图：只认脸、发型和服装，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，双人镜头，两人都在画面里，50mm 标准镜头，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，右手始终握着一支银色有线话筒，话筒线垂下来，两位选手放下话筒，隔着舞台互相看着，嘴角都挑了一下，嘴闭着，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u40.png`
用途：u40 首帧（s11_outro · crowd）

上传：图1 = `refs/crowd.png`（场景图：保持同一个场馆、灯光、配色和观众席）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, 看台上层层叠叠坐满了观众，挥着红色荧光棒，挥手欢呼; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 crowd.png（观众席中景）：保持同一个场馆、同样的灯光、配色和观众席，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，看台上层层叠叠坐满了观众，挥着红色荧光棒，挥手欢呼，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 crowd.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u41.png`
用途：u41 首帧（s11_outro · establish）

上传：图1 = `refs/venue_high.png`（场景图：保持同一个场馆、灯光、配色和观众席）

Midjourney EN：
```
wide shot, 24mm wide lens very close to the face, natural wide-angle perspective, 场馆高位全景，全场观众站起来挥手，台上两队站在八卦图案两边; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue_high.png（场馆高位全景）：保持同一个场馆、同样的灯光、配色和观众席，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，全景，24mm 广角镜头离人物很近，人物几乎贴着镜头，背景有自然的广角透视，场馆高位全景，全场观众站起来挥手，台上两队站在八卦图案两边，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue_high.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u42.png`
用途：u42 首帧（s11_outro · host）

上传：图1 = `refs/dj_booth.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/xu_san_sheet.png`（徐三的锁定定妆组图）

Midjourney EN：
```
close-up, 135mm telephoto, compressed space, crowd and lights melted into large bokeh, broadcast long-lens camera, a 38-year-old Chinese man, medium build, a calm oval face, thin rectangular glasses, short black hair with a light choppy fringe over the forehead, clean-shaven with a faint shadow, a composed half smile, real skin with pores and fine lines on the forehead, a slim black suit jacket with the sleeves pushed up, a white shirt with the collar open and no tie, black trousers, a black leather belt, large black headphones around his neck, no lettering, DJ 双手举过头顶，跟着观众一起喊; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 dj_booth.png（DJ 台）：保持同一个场馆、同样的灯光、配色和观众席，图2是徐三的锁定定妆组图：只认脸、发型和服装，特写，头和肩膀，135mm 长焦镜头，空间被压缩，背景的观众和灯虚成大片光斑，像综艺直播的长焦机位，38 岁的中国男人，中等身材，神情沉稳，戴细框长方形眼镜；黑色短发，碎刘海垂在额前；胡子刮净有淡青色，嘴角半笑；皮肤有毛孔，额头细纹，修身黑西装外套推着袖子，白衬衫敞领不打领带，黑西裤，脖子上挂一副黑色大耳机；衣服上没有文字，站在DJ台后面，一只手搭在唱盘上，DJ 双手举过头顶，跟着观众一起喊，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 dj_booth.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u43.png`
用途：u43 首帧（s11_outro · outro）

上传：图1 = `refs/venue.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/a_sheet.png`（诸葛青的锁定定妆组图）

Midjourney EN：
```
two-shot, 50mm lens, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, 两位选手放下话筒，隔着舞台互相看着，嘴角都挑了一下，嘴闭着; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue.png（舞台正面）：保持同一个场馆、同样的灯光、配色和观众席，图2是诸葛青的锁定定妆组图：只认脸、发型和服装，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，双人镜头，两人都在画面里，50mm 标准镜头，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，右手始终握着一支银色有线话筒，话筒线垂下来，两位选手放下话筒，隔着舞台互相看着，嘴角都挑了一下，嘴闭着，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue.png 当 --sref 风格参考，或者用即梦上传它当图1。

### `plate_u44.png`
用途：u44 首帧（s11_outro · outro）

上传：图1 = `refs/venue.png`（场景图：保持同一个场馆、灯光、配色和观众席）；图2 = `refs/a_sheet.png`（诸葛青的锁定定妆组图）

Midjourney EN：
```
two-shot, 50mm lens, a 24-year-old Chinese man, slim and long-limbed, a narrow oval face with a soft jaw and an easy smile, eyes always narrowed into two smiling curves, dark navy-blue hair with a long layered side fringe falling over one brow and the back trimmed to the nape, styled with a little texture, light on-camera stage makeup, real skin with fine pores and a faint mole under the left eye, a crisp white open-collar shirt with the top two buttons undone, slim dark brown suspenders, an open charcoal tailored blazer with fine tone-on-tone bagua line embroidery on the lapels, slim black trousers, black leather boots, a green jade pendant on a thin black cord, a thin silver ring, plain fabric with no lettering, 两位选手放下话筒，隔着舞台互相看着，嘴角都挑了一下，嘴闭着; a TV rap variety show arena rebuilt from the Luotian tournament ring at night: a black square stage, a giant taiji-bagua floor graphic with no lettering, a full red LED wall and red light strips, tiered seats packed with people, the dark silhouette of Longhu Mountain at night through an opening at the back, indoor rap variety show arena rebuilt from a Taoist tournament ring at night, black square stage, a giant taiji-bagua pattern on the floor with no lettering, a full red LED wall and red light strips behind, tiered audience, hard top stage light with red side light, thin haze, long lens melting crowd and lights into bokeh, broadcast realism with fine grain, on-camera adult performer with pleasant, well-proportioned features, real skin with fine pores, natural skin tone variation, a natural sheen and fine sweat under the stage lights, light TV-show makeup, real micro-expressions, an original face that does not resemble any real celebrity or actor, real creased fabric, no text, no letters, no logos --ar 16:9 --style raw --stylize 60 --no cgi, 3d render, plastic skin, airbrushed, wax figure, doll, figurine, porcelain, anime, illustration, oversaturated, text, letters, logo, watermark
```
即梦 CN：
```
图1是场景图 venue.png（舞台正面）：保持同一个场馆、同样的灯光、配色和观众席，图2是诸葛青的锁定定妆组图：只认脸、发型和服装，看台上层层叠叠坐满了观众，挥着红色荧光棒，没有空座位，每个人长得都不一样，双人镜头，两人都在画面里，50mm 标准镜头，24 岁的中国男人，瘦高，鹅蛋脸，嘴角总挂着笑；眼睛一直眯成两道弯弯的笑线；深藏青色头发，长侧刘海斜盖住一边眉毛，后面剪到后颈；上镜淡妆，皮肤有毛孔，左眼下一颗淡痣，白色敞领衬衫，深棕色细背带，敞穿深炭灰修身西装外套（翻领暗纹八卦线），黑色窄腿裤，黑皮靴，黑细绳挂绿色玉坠；衣服上没有文字，右手始终握着一支银色有线话筒，话筒线垂下来，两位选手放下话筒，隔着舞台互相看着，嘴角都挑了一下，嘴闭着，罗天大醮的擂台改成的电视台说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（没有文字），背后红色 LED 大屏和一圈红色灯带，观众席层层叠叠，后方开口里隐约是夜色中龙虎山的山影，罗天大醮的擂台改成的室内说唱综艺场馆，夜晚：黑色方形擂台，地面是巨大的太极八卦图案（上面没有任何文字），背后一整面红色 LED 大屏和一圈红色灯带，观众席层层叠叠；主光是舞台顶部的硬光，两侧打红色侧光，空气里有薄烟；长焦机位把观众和灯虚成光斑，像电视直播画面但有电影感，细腻颗粒，真人综艺节目现场实拍质感，像电视台多机位直播里截下来的画面，不是 CG、不是游戏、不是动画。人物是上镜、五官端正耐看的成年演员，年龄以角色设定为准；皮肤是真实的：细小毛孔、自然的肤色变化，舞台灯下有自然的油光和细汗，化的是综艺节目的淡妆；不磨皮，皮肤不能光滑得像塑料、蜡像或手办。表情有真实的微表情：眨眼、抿嘴、挑眉、忍笑。每张脸都是原创面孔，不像任何真实的明星或演员。服装是真实的布料，有褶皱和穿着痕迹，综艺节目现场照片，无文字、无水印、无标志。
```
Midjourney 里把锁定的 venue.png 当 --sref 风格参考，或者用即梦上传它当图1。
