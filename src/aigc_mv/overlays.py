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
        elif self.style == "battle_hud":
            hans = [i for i, c in enumerate(shown) if "\u4e00" <= c <= "\u9fff"]
            cut = hans[-2] if len(hans) >= 2 else 0
            head, tail = shown[:cut], shown[cut:]
            fh = self._fit(d, shown, "sans", 54, "Black", W - 280 * S)
            ft = _font("brush", int(fh.size * 1.24))
            wh, wt = d.textlength(head, font=fh), d.textlength(tail, font=ft)
            total_w = wh + wt
            base = int(H * (0.882 if note else 0.918))
            x = (W - total_w) / 2
            pad_x, bar_h = int(28 * S), int(70 * S)
            hud = self.canvas()
            hd = ImageDraw.Draw(hud)
            bx0, by0 = int(x - pad_x), int(base - 52 * S)
            bx1, by1 = int(x + total_w + pad_x), int(by0 + bar_h)
            hd.rounded_rectangle([bx0, by0, bx1, by1], radius=int(10 * S), fill=(12, 14, 20, 178),
                                 outline=(220, 38, 38, 210), width=max(1, int(2 * S)))
            hd.rectangle([bx0, by0, bx0 + int(7 * S), by1], fill=(220, 38, 38, 245))
            img.alpha_composite(hud)
            img.alpha_composite(self._brush(int(wt + 36 * S), int(48 * S), seed),
                                (int(x + wh - 14 * S), int(base - 36 * S)))
            d.text((x, base), head, font=fh, fill=(255, 255, 255, 255), anchor="ls",
                   stroke_width=max(2, int(3 * S)), stroke_fill=(10, 10, 14, 235))
            d.text((x + wh, base + int(2 * S)), tail, font=ft, fill=GOLD, anchor="ls",
                   stroke_width=max(2, int(4 * S)), stroke_fill=INK)
        else:
            f = self._fit(d, shown, "sans", 54, "Bold", W - 240 * S)
            base = int(H * (0.885 if note else 0.925))
            d.text((W / 2, base), shown, font=f, fill=(255, 255, 255, 255), anchor="ms",
                   stroke_width=max(2, int(3 * S)), stroke_fill=(10, 10, 10, 230))
        if note:
            label = f"◆ 典故  {note}" if self.style == "battle_hud" and not note.startswith("◆") else note
            fn = self._fit(d, label, "sans", 28 if self.style == "battle_hud" else 30, "Medium", W - 200 * S)
            if self.style == "battle_hud":
                nw = d.textlength(label, font=fn)
                pill = self.canvas()
                pd = ImageDraw.Draw(pill)
                py = int(H * 0.955)
                pd.rounded_rectangle(
                    [W / 2 - nw / 2 - 16 * S, py - 28 * S, W / 2 + nw / 2 + 16 * S, py + 8 * S],
                    radius=int(8 * S), fill=(18, 18, 24, 195), outline=(255, 212, 92, 160), width=max(1, int(1.5 * S)),
                )
                img.alpha_composite(pill)
            d.text((W / 2, int(H * 0.955)), label, font=fn,
                   fill=(255, 232, 150, 245) if self.style == "battle_hud" else (235, 235, 235, 240),
                   anchor="ms", stroke_width=max(1, int(2 * S)), stroke_fill=(0, 0, 0, 220))
        img.alpha_composite(self._shadow(layer, 4, 0.5))
        return img

    def lyric_karaoke(self, text: str, progress: float, singer: str = "",
                      accent: tuple[int, int, int] = (220, 38, 38), note: str = "", seed: int = 0) -> Image.Image:
        """24fps Battle-HUD kinetic karaoke subtitle: progressive gold wipe + 1.24x punchword pop + speaker tag."""
        S, W, H = self.S, self.W, self.H
        p = max(0.0, min(1.0, float(progress)))
        shown = text.replace(" ", "  ")
        hans = [i for i, c in enumerate(shown) if "\u4e00" <= c <= "\u9fff"]
        cut = hans[-2] if len(hans) >= 2 else len(shown)
        head, tail = shown[:cut], shown[cut:]

        img, base_layer, hi_layer = self.canvas(), self.canvas(), self.canvas()
        db, dh = ImageDraw.Draw(base_layer), ImageDraw.Draw(hi_layer)
        fh = self._fit(db, shown, "sans", 54, "Black", W - 280 * S)
        # Spring pop on the tail punchword once progress crosses 0.72
        pop = 1.24 + (0.06 if 0.72 <= p <= 0.88 else 0.0)
        ft = _font("brush", int(fh.size * pop))
        wh, wt = db.textlength(head, font=fh), db.textlength(tail, font=ft)
        total_w = wh + wt
        base_y = int(H * (0.882 if note else 0.918))
        x = (W - total_w) / 2

        hud = self.canvas()
        hd = ImageDraw.Draw(hud)
        bx0, by0 = int(x - 28 * S), int(base_y - 52 * S)
        bx1, by1 = int(x + total_w + 28 * S), int(by0 + 70 * S)
        hd.rounded_rectangle([bx0, by0, bx1, by1], radius=int(10 * S), fill=(12, 14, 20, 182),
                             outline=(*accent, 215), width=max(1, int(2 * S)))
        hd.rectangle([bx0, by0, bx0 + int(8 * S), by1], fill=(*accent, 250))
        if singer:
            fs = _font("sans", int(24 * S), "Black")
            sw = hd.textlength(singer, font=fs)
            hd.rounded_rectangle([bx0, by0 - int(32 * S), bx0 + sw + int(24 * S), by0 - int(2 * S)],
                                 radius=int(6 * S), fill=(*accent, 235))
            hd.text((bx0 + int(12 * S), by0 - int(8 * S)), singer, font=fs, fill=(255, 255, 255, 255), anchor="ls")
        img.alpha_composite(hud)
        if tail:
            img.alpha_composite(self._brush(int(wt + 36 * S), int(48 * S), seed),
                                (int(x + wh - 14 * S), int(base_y - 36 * S)))

        # Unsung base text (crisp silver-white) and sung highlight text (warm gold)
        for drw, col_h, col_t in (
            (db, (232, 236, 244, 245), (255, 242, 200, 250)),
            (dh, GOLD, (255, 215, 64, 255)),
        ):
            drw.text((x, base_y), head, font=fh, fill=col_h, anchor="ls",
                     stroke_width=max(2, int(3 * S)), stroke_fill=(10, 10, 14, 235))
            if tail:
                drw.text((x + wh, base_y + int(2 * S)), tail, font=ft, fill=col_t, anchor="ls",
                         stroke_width=max(2, int(4 * S)), stroke_fill=INK)

        wipe_x = int(x + total_w * p)
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).rectangle([0, 0, wipe_x, H], fill=255)
        merged_txt = Image.composite(hi_layer, base_layer, mask)
        img.alpha_composite(self._shadow(merged_txt, 4, 0.5))
        if note:
            label = f"◆ 典故  {note}" if not note.startswith("◆") else note
            fn = self._fit(ImageDraw.Draw(img), label, "sans", 28, "Medium", W - 200 * S)
            ImageDraw.Draw(img).text((W / 2, int(H * 0.955)), label, font=fn, fill=(255, 232, 150, 245),
                                     anchor="ms", stroke_width=max(1, int(2 * S)), stroke_fill=(0, 0, 0, 220))
        return img

    def seal_badge(self, name: str, faction: str = "", right: bool = False,
                   accent: tuple[int, int, int] = (205, 28, 36)) -> Image.Image:
        """Chinese seal + brush character entrance badge (`三一门 · 陆瑾` / `全性 · 李慕玄`)."""
        S, W, H = self.S, self.W, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        fn = _font("brush", int(104 * S))
        ff = _font("sans", int(30 * S), "Black")
        x = W - int(130 * S) if right else int(130 * S)
        anc = "rs" if right else "ls"
        y = int(H * 0.74)
        if faction:
            fw = d.textlength(faction, font=ff)
            sx0 = int(x - fw - 28 * S) if right else int(x)
            sy0 = int(y - 128 * S)
            d.rounded_rectangle([sx0, sy0, int(sx0 + fw + 28 * S), int(sy0 + 42 * S)],
                                radius=int(6 * S), fill=(*accent, 235), outline=(255, 236, 185, 230),
                                width=max(1, int(2 * S)))
            d.text((sx0 + (fw + 28 * S) / 2, sy0 + 21 * S), faction, font=ff, fill=(255, 248, 230, 255), anchor="mm")
        d.text((x, y), name, font=fn, fill=GOLD, anchor=anc, stroke_width=max(2, int(4 * S)), stroke_fill=INK)
        img.alpha_composite(self._shadow(layer, 5, 0.6))
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

    def show_title(self, show_name: str, episode_no: str, a: str, b: str, disclaimer: str) -> Image.Image:
        """Programme logo card for the cold open: show name large, episode number, 'A VS B', disclaimer."""
        S, W, H = self.S, self.W, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        red = (220, 30, 36, 255)
        f_show = self._fit(d, show_name, "brush", 180, "Regular", W - 200 * S)
        d.text((W / 2, int(H * 0.40)), show_name, font=f_show, fill=(255, 255, 255, 255), anchor="ms",
               stroke_width=int(7 * S), stroke_fill=(150, 10, 16, 255))
        if episode_no:
            fe = _font("sans", int(44 * S), "Black")
            tw = d.textlength(episode_no, font=fe)
            y = int(H * 0.47)
            d.rectangle([W / 2 - tw / 2 - 22 * S, y - 46 * S, W / 2 + tw / 2 + 22 * S, y + 12 * S], fill=red)
            d.text((W / 2, y), episode_no, font=fe, fill=(255, 255, 255, 255), anchor="ms")
        vs = f"{a}  VS  {b}"
        fv = self._fit(d, vs, "sans", 76, "Black", W - 240 * S)
        d.text((W / 2, int(H * 0.60)), vs, font=fv, fill=(255, 255, 255, 255), anchor="ms",
               stroke_width=int(4 * S), stroke_fill=(10, 10, 10, 230))
        d.text((W / 2, int(H * 0.67)), disclaimer, font=_font("sans", int(32 * S), "Bold"),
               fill=(240, 240, 240, 255), anchor="ms", stroke_width=int(2 * S), stroke_fill=INK)
        img.alpha_composite(self._shadow(layer, 8, 0.7))
        return img

    def logo_bug(self, text: str) -> Image.Image:
        """Small programme badge in the bottom-right corner (the reference's corner logo)."""
        S, W, H = self.S, self.W, self.H
        img = self.canvas()
        d = ImageDraw.Draw(img)
        f = _font("sans", int(30 * S), "Black")
        tw = d.textlength(text, font=f)
        pad = 14 * S
        x1, y1 = W - 48 * S, H - 40 * S
        x0, y0 = x1 - tw - 2 * pad, y1 - 52 * S
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(8 * S), fill=(200, 20, 28, 210),
                            outline=(255, 255, 255, 230), width=max(1, int(3 * S)))
        d.text(((x0 + x1) / 2, (y0 + y1) / 2), text, font=f, fill=(255, 255, 255, 245), anchor="mm")
        return img

    def lower_third(self, name: str, title: str) -> Image.Image:
        """Name + caption, bottom-left, above the subtitle zone (judges / hosts / cameos)."""
        S, H = self.S, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        fn, ft = _font("sans", int(56 * S), "Black"), _font("sans", int(30 * S), "Bold")
        x, y = int(90 * S), int(H * 0.78)
        wn = d.textlength(name, font=fn)
        wt = d.textlength(title, font=ft) if title else 0
        d.rectangle([x - 18 * S, y - 64 * S, x - 8 * S, y + (46 if title else 6) * S], fill=(220, 30, 36, 255))
        d.text((x, y), name, font=fn, fill=(255, 255, 255, 255), anchor="ls", stroke_width=max(2, int(3 * S)),
               stroke_fill=(10, 10, 10, 220))
        if title:
            d.rectangle([x - 4 * S, y + 8 * S, x + max(wn, wt) + 16 * S, y + 46 * S], fill=(15, 15, 15, 190))
            d.text((x + 6 * S, y + 38 * S), title, font=ft, fill=(255, 255, 255, 240), anchor="ls")
        img.alpha_composite(self._shadow(layer, 4, 0.5))
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
