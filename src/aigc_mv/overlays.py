"""Text layers drawn with Pillow as transparent PNGs (ffmpeg drawtext often lacks fontconfig).

Two subtitle styles:
- ``broadcast``: white bold sans with a thin dark outline, low and centred – the 综艺 / 火影有嘻哈 look; reads as
  a real TV edit rather than a template.
- ``gold``: gold serif with the last two characters enlarged on a red brush stroke (ancient-rap-battle).
Every lyric may carry a source note (史料注释) in a smaller line below.
"""

from __future__ import annotations

import os
import random
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

CACHE = Path(os.environ.get("AIGC_MV_CACHE", Path.home() / ".cache" / "aigc-mv"))
FONTS = {  # SIL Open Font License, Google Fonts repository
    "sans": ("NotoSansSC.ttf", "https://github.com/google/fonts/raw/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"),
    "serif": ("NotoSerifSC.ttf", "https://github.com/google/fonts/raw/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf"),
    "brush": ("MaShanZheng.ttf", "https://github.com/google/fonts/raw/main/ofl/mashanzheng/MaShanZheng-Regular.ttf"),
}
LOCAL = {
    "sans": ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/System/Library/Fonts/PingFang.ttc",
             "C:/Windows/Fonts/msyhbd.ttc"],
    "serif": ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc", "C:/Windows/Fonts/simsun.ttc"],
    "brush": [],
}
GOLD = (255, 228, 92, 255)
INK = (30, 16, 0, 255)


def font_path(kind: str) -> Path:
    env = os.environ.get(f"AIGC_MV_FONT_{kind.upper()}")
    if env and Path(env).is_file():
        return Path(env)
    for p in LOCAL.get(kind, []):
        if Path(p).is_file():
            return Path(p)
    name, url = FONTS[kind]
    dst = CACHE / "fonts" / name
    if not dst.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, dst)
    return dst


def _font(kind: str, size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(font_path(kind)), max(8, size))
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


class Sheet:
    def __init__(self, w: int, h: int, style: str = "broadcast"):
        self.W, self.H, self.S, self.style = w, h, w / 1920, style

    def canvas(self) -> Image.Image:
        return Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))

    def _shadow(self, layer: Image.Image, blur: float = 5, alpha: float = 0.6) -> Image.Image:
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        sh.putalpha(layer.split()[3].point(lambda v: int(v * alpha)))
        out = self.canvas()
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur * self.S)), (int(2 * self.S), int(3 * self.S)))
        out.alpha_composite(layer)
        return out

    def _fit(self, d: ImageDraw.ImageDraw, text: str, kind: str, size: int, weight: str, max_w: float):
        f = _font(kind, int(size * self.S), weight)
        while d.textlength(text, font=f) > max_w and f.size > 12:
            f = _font(kind, f.size - 2, weight)
        return f

    def _brush(self, w: int, h: int, seed: int) -> Image.Image:
        rnd = random.Random(seed)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i in range(int(h * 0.9)):
            x0 = int(rnd.uniform(0, 0.06) * w)
            x1 = int(w - rnd.uniform(0, 0.12) * w - 0.18 * w * (i / h) ** 2)
            d.line([(x0, int(h * 0.05) + i), (x1, int(h * 0.05) + i)], fill=(190, 18, 24, int(rnd.uniform(150, 235))))
        return im.filter(ImageFilter.GaussianBlur(1.2))

    def lyric(self, text: str, note: str = "", seed: int = 0) -> Image.Image:
        S, W, H = self.S, self.W, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        shown = text.replace(" ", "  ")
        if self.style == "gold":
            hans = [i for i, c in enumerate(shown) if "\u4e00" <= c <= "\u9fff"]
            cut = hans[-2] if len(hans) >= 2 else 0
            head, tail = shown[:cut], shown[cut:]
            fh, ft = _font("serif", int(60 * S), "Black"), _font("serif", int(84 * S), "Black")
            wh, wt = d.textlength(head, font=fh), d.textlength(tail, font=ft)
            base = int(H * (0.885 if note else 0.92))
            x = (W - wh - wt) / 2
            img.alpha_composite(self._brush(int(wt + 46 * S), int(52 * S), seed), (int(x + wh - 20 * S), int(base - 34 * S)))
            d.text((x, base), head, font=fh, fill=GOLD, anchor="ls", stroke_width=int(3 * S), stroke_fill=INK)
            d.text((x + wh, base), tail, font=ft, fill=GOLD, anchor="ls", stroke_width=int(4 * S), stroke_fill=INK)
        else:
            f = self._fit(d, shown, "sans", 54, "Bold", W - 240 * S)
            base = int(H * (0.885 if note else 0.925))
            d.text((W / 2, base), shown, font=f, fill=(255, 255, 255, 255), anchor="ms",
                   stroke_width=max(2, int(3 * S)), stroke_fill=(10, 10, 10, 230))
        if note:
            fn = self._fit(d, note, "sans", 30, "Medium", W - 200 * S)
            d.text((W / 2, int(H * 0.955)), note, font=fn, fill=(235, 235, 235, 240), anchor="ms",
                   stroke_width=max(1, int(2 * S)), stroke_fill=(0, 0, 0, 220))
        img.alpha_composite(self._shadow(layer, 4, 0.5))
        return img

    def name(self, name: str, aka: str, right: bool) -> Image.Image:
        S, W, H = self.S, self.W, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        x = W - int(140 * S) if right else int(140 * S)
        anc = "rs" if right else "ls"
        d.text((x, int(H * 0.76)), name, font=_font("brush", int(110 * S)), fill=GOLD, anchor=anc,
               stroke_width=int(3 * S), stroke_fill=INK)
        if aka:
            d.text((x, int(H * 0.805)), f"aka {aka}", font=_font("sans", int(34 * S), "Bold"),
                   fill=(250, 236, 190, 255), anchor=anc, stroke_width=int(2 * S), stroke_fill=INK)
        img.alpha_composite(self._shadow(layer))
        return img

    def title(self, a: str, b: str, disclaimer: str) -> Image.Image:
        S, W, H = self.S, self.W, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        br = _font("brush", int(170 * S))
        vs = _font("sans", int(110 * S), "Black")
        wa, wv, wb = d.textlength(a, font=br), d.textlength(" VS ", font=vs), d.textlength(b, font=br)
        x = (W - wa - wv - wb) / 2
        y = int(H * 0.47)
        d.text((x, y), a, font=br, fill=GOLD, anchor="ls", stroke_width=int(6 * S), stroke_fill=INK)
        d.text((x + wa, y), " VS ", font=vs, fill=(220, 30, 36, 255), anchor="ls", stroke_width=int(5 * S),
               stroke_fill=INK)
        d.text((x + wa + wv, y), b, font=br, fill=GOLD, anchor="ls", stroke_width=int(6 * S), stroke_fill=INK)
        d.text((W / 2, int(H * 0.58)), disclaimer, font=_font("sans", int(38 * S), "Bold"),
               fill=(250, 240, 220, 255), anchor="ms", stroke_width=int(2 * S), stroke_fill=INK)
        img.alpha_composite(self._shadow(layer, 8, 0.7))
        return img

    def end(self, l1: str, l2: str) -> Image.Image:
        S, W, H = self.S, self.W, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        br = _font("brush", int(140 * S))
        d.text((W / 2, int(H * 0.42)), l1, font=br, fill=GOLD, anchor="ms", stroke_width=int(6 * S), stroke_fill=INK)
        d.text((W / 2, int(H * 0.58)), l2, font=br, fill=GOLD, anchor="ms", stroke_width=int(6 * S), stroke_fill=INK)
        img.alpha_composite(self._shadow(layer, 8, 0.7))
        return img

    def watermark(self, text: str) -> Image.Image:
        S, W = self.S, self.W
        img, layer = self.canvas(), self.canvas()
        ImageDraw.Draw(layer).text((W - int(56 * S), int(72 * S)), text, font=_font("sans", int(34 * S), "Bold"),
                                   fill=(255, 255, 255, 200), anchor="rs", stroke_width=int(2 * S),
                                   stroke_fill=(0, 0, 0, 160))
        img.alpha_composite(self._shadow(layer))
        return img

    def card(self, lines: list[str], bg=(28, 30, 38)) -> Image.Image:
        """Opaque placeholder frame for shots without a plate or take (animatic)."""
        img = Image.new("RGB", (self.W, self.H), bg)
        d = ImageDraw.Draw(img)
        y = int(self.H * 0.36)
        for i, t in enumerate(lines):
            f = self._fit(d, t, "sans", 52 if i == 0 else 34, "Bold" if i == 0 else "Regular", self.W - 160 * self.S)
            d.text((int(80 * self.S), y), t, font=f, fill=(235, 235, 235) if i == 0 else (180, 188, 200))
            y += int((70 if i == 0 else 50) * self.S)
        return img
