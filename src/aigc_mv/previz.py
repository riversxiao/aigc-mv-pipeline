"""Free previz: a synthetic beat track and Pillow-drawn placeholder plates, so a whole episode can be cut,
timed and reviewed before a single paid generation.

- `synth_beat(timing, out_wav)`: 44.1 kHz stereo boom-bap on the episode's beat grid (kick on 1 / 3, snare on
  2 / 4, hats on the 8ths, a short riser before every section) plus a soft pitched blip on every lyric
  syllable (`TimedLine.chars`), a different pitch per singer, so the lip timing can be heard.
- `shot_plate(ep, shot, size, timing)`: a stylised red / black arena (LED wall, red light strip, crowd bokeh,
  the taiji-bagua floor) with labelled coloured silhouettes placed by the shot's staging (rappers on their
  side, the crew small and blurred behind, judges on three thrones, the DJ booth, the hook singer at a stand
  mic, split screen, the blackout spot, the empty stage). Top-left label: shot id, staging, framing, camera.

Placeholders live under edit/ only: they are never written to refs/ and never uploaded.
"""

from __future__ import annotations

import math
import random
import zlib
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter

from aigc_mv import cinema
from aigc_mv.board import BoardShot
from aigc_mv.episode import Episode
from aigc_mv.overlays import _font
from aigc_mv.timing import Timing

SR = 44100

# --------------------------------------------------------------------------- beat

ROLE_PITCH = {"rapper": 0.0, "teammate": 330.0, "judge": 196.0, "host": 294.0, "dj": 349.0, "hook": 523.0,
              "cameo": 262.0}


def _pitch(ep: Episode | None, who: str) -> float:
    if ep is None or who not in ep.cast:
        return 220.0 + (zlib.crc32(who.encode()) % 8) * 30.0
    c = ep.cast[who]
    if c.role == "rapper":
        return 220.0 if c.side == "left" else 165.0
    return ROLE_PITCH.get(c.role, 260.0)


def _env(n: int, decay: float) -> np.ndarray:
    return np.exp(-np.arange(n) / (decay * SR)).astype(np.float32)


def _add(buf: np.ndarray, t: float, sig: np.ndarray, pan: float = 0.0) -> None:
    a = int(round(t * SR))
    if a >= len(buf) or a + len(sig) <= 0:
        return
    s0 = max(0, -a)
    a = max(0, a)
    seg = sig[s0: s0 + len(buf) - a]
    buf[a: a + len(seg), 0] += seg * (1 - max(0.0, pan))
    buf[a: a + len(seg), 1] += seg * (1 + min(0.0, pan))


def synth_beat(timing: Timing, out_wav: Path, ep: Episode | None = None) -> Path:
    """Write the previz track (song length, beats on the grid, a blip on every sung syllable)."""
    rng = np.random.default_rng(7)
    n = int(round(timing.duration * SR))
    buf = np.zeros((n, 2), np.float32)
    beat = 60.0 / timing.grid.bpm
    t = np.arange(int(0.35 * SR)) / SR
    kick = (np.sin(2 * np.pi * (45 * t + 60 * (1 - np.exp(-t / 0.04)) * 0.04)) * _env(len(t), 0.09)).astype(np.float32)
    kick += 0.3 * np.sin(2 * np.pi * 50 * t).astype(np.float32) * _env(len(t), 0.18)
    ns = int(0.2 * SR)
    snare = (rng.standard_normal(ns).astype(np.float32) * _env(ns, 0.05) * 0.55
             + 0.35 * np.sin(2 * np.pi * 185 * np.arange(ns) / SR).astype(np.float32) * _env(ns, 0.04))
    nh = int(0.05 * SR)
    hat = np.diff(rng.standard_normal(nh + 1)).astype(np.float32) * _env(nh, 0.012) * 0.18

    downs = timing.grid.downbeats or timing.grid.beats[:1]
    for b in timing.grid.beats:
        prev = [d for d in downs if d <= b + 1e-3]
        pos = int(round((b - prev[-1]) / beat)) % 4 if prev else 0
        if pos in (0, 2):
            _add(buf, b, kick * 0.9)
        else:
            _add(buf, b, snare * 0.7)
        _add(buf, b, hat, 0.3)
        _add(buf, b + beat / 2, hat * 0.7, 0.3)
    # a short riser into every section (noise swelling + a rising tone over one beat and a half)
    for sec in timing.sections[1:]:
        L = int(1.5 * beat * SR)
        tt = np.arange(L) / SR
        sweep = np.sin(2 * np.pi * (300 * tt + 500 * tt ** 2 / (1.5 * beat))).astype(np.float32)
        swell = np.linspace(0, 1, L, dtype=np.float32) ** 2
        riser = (0.12 * sweep + 0.10 * rng.standard_normal(L).astype(np.float32)) * swell
        _add(buf, sec.t0 - L / SR, riser)
    # syllable blips: the lip timing made audible
    for ln in timing.lines:
        f = _pitch(ep, ln.who)
        L = int((0.07 if ln.spoken else 0.11) * SR)
        tt = np.arange(L) / SR
        tone = np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)
        if ln.spoken:  # spoken lines: a drier, buzzier tick
            tone = np.sign(tone) * 0.6 + 0.4 * tone
        blip = (0.16 * tone * np.hanning(L)).astype(np.float32)
        for c in ln.chars:
            _add(buf, c, blip)
    peak = float(np.abs(buf).max()) or 1.0
    buf *= 0.9 / peak
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_wav, buf, SR, subtype="PCM_16")
    return out_wav


# --------------------------------------------------------------------------- plates

PALETTE = [(70, 140, 245), (245, 166, 40), (90, 205, 120), (205, 90, 210), (240, 220, 80), (90, 210, 225),
           (235, 115, 90), (160, 160, 255), (255, 140, 190), (150, 220, 90), (205, 170, 120), (120, 185, 165),
           (225, 125, 45), (145, 115, 225), (105, 165, 235), (230, 95, 145)]

# framing -> (head radius, head centre y) as fractions of the frame height
FIG = {"ECU": (0.30, 0.46), "CU": (0.19, 0.42), "MCU": (0.14, 0.38), "MS": (0.10, 0.36), "OTS": (0.13, 0.38),
       "2S": (0.10, 0.38), "MWS": (0.07, 0.42), "WS": (0.035, 0.64)}
BLUR = {"ECU": 12, "CU": 10, "MCU": 8, "MS": 5, "OTS": 8, "2S": 4, "MWS": 2, "WS": 1}


def colour(ep: Episode, key: str) -> tuple[int, int, int]:
    keys = list(ep.cast)
    i = keys.index(key) if key in keys else zlib.crc32(key.encode())
    return PALETTE[i % len(PALETTE)]


def _x_of(ep: Episode, key: str) -> float:
    side = ep.cast[key].side if key in ep.cast else "center"
    return {"left": 0.34, "right": 0.66}.get(side, 0.5)


class _Plate:
    def __init__(self, ep: Episode, shot: BoardShot, size: tuple[int, int]):
        self.ep, self.shot = ep, shot
        self.W, self.H = size
        self.S = self.W / 1920
        self.rnd = random.Random(zlib.crc32(shot.id.encode()))
        self.img = Image.new("RGB", size, (0, 0, 0))

    # ------------------------------------------------------------ background

    def arena(self, blur: float, crowd: float = 1.0, floor: bool = True, wall: bool = True) -> None:
        W, H = self.W, self.H
        bg = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(bg)
        for y in range(H):  # top: deep red, fading to black
            k = max(0.0, 1 - y / (0.62 * H))
            d.line([(0, y), (W, y)], fill=(int(70 * k) + 6, int(4 * k) + 4, int(8 * k) + 6))
        if wall:
            cols = 26
            cw = W / cols
            for i in range(cols):
                v = self.rnd.uniform(0.35, 1.0)
                d.rectangle([i * cw + cw * 0.12, 0.05 * H, (i + 1) * cw - cw * 0.12, 0.43 * H],
                            fill=(int(200 * v), int(20 * v), int(28 * v)))
            d.rectangle([0, 0.455 * H, W, 0.47 * H], fill=(255, 40, 50))
        for _ in range(int(160 * crowd)):  # crowd tiers melted into bokeh
            x, y = self.rnd.uniform(0, W), self.rnd.uniform(0.47 * H, 0.72 * H)
            r = self.rnd.uniform(3, 11) * self.S * (1 + blur / 6)
            c = self.rnd.choice([(255, 225, 190), (255, 70, 70), (255, 160, 120), (200, 200, 230)])
            k = self.rnd.uniform(0.25, 0.8)
            d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * k) for v in c))
        if floor:
            self.taiji(d, W / 2, 0.86 * H, 0.44 * W, 0.13 * H, (60, 60, 66))
        self.img = bg.filter(ImageFilter.GaussianBlur(blur * self.S)) if blur else bg

    def taiji(self, d: ImageDraw.ImageDraw, cx: float, cy: float, rx: float, ry: float, col) -> None:
        """Flattened taiji-bagua floor: outer ring, eight trigram dashes, the two halves."""
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=col, width=max(2, int(4 * self.S)))
        for k in range(8):
            a = k * math.pi / 4
            px, py = cx + 0.86 * rx * math.cos(a), cy + 0.86 * ry * math.sin(a)
            for j in range(3):
                w = 0.05 * rx
                o = (j - 1) * 0.045 * ry
                d.line([(px - w, py + o), (px + w, py + o)], fill=col, width=max(1, int(3 * self.S)))
        ir, iry = 0.5 * rx, 0.5 * ry
        d.pieslice([cx - ir, cy - iry, cx + ir, cy + iry], 90, 270, fill=tuple(min(255, v + 70) for v in col))
        d.pieslice([cx - ir, cy - iry, cx + ir, cy + iry], 270, 90, fill=(18, 18, 20))

    # ------------------------------------------------------------ people

    def figure(self, key: str, x: float, framing: str, scale: float = 1.0, dy: float = 0.0, blur: float = 0.0,
               dark: bool = False, label: bool = True, head_down: bool = False) -> None:
        W, H = self.W, self.H
        r0, hy0 = FIG.get(framing, FIG["MCU"])
        r, hy = r0 * H * scale, (hy0 + dy) * H + (0.05 * H if head_down else 0)
        cx = x * W
        col = (14, 14, 16) if dark else colour(self.ep, key)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        body = tuple(int(v * 0.72) for v in col)
        d.rounded_rectangle([cx - 1.7 * r, hy + 1.05 * r, cx + 1.7 * r, hy + 7.5 * r], radius=int(0.8 * r),
                            fill=body + (255,))
        d.rectangle([cx - 0.35 * r, hy + 0.7 * r, cx + 0.35 * r, hy + 1.3 * r], fill=body + (255,))
        d.ellipse([cx - r, hy - r, cx + r, hy + r], fill=col + (255,))
        if label and not dark and key in self.ep.cast:
            name = self.ep.cast[key].name_cn
            f = _font("sans", max(12, int(0.42 * r)), "Bold")
            d.text((cx, hy + 2.2 * r), name, font=f, fill=(255, 255, 255, 240), anchor="mm",
                   stroke_width=max(1, int(0.05 * r)), stroke_fill=(0, 0, 0, 200))
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur * self.S))
        base = self.img.convert("RGBA")
        base.alpha_composite(layer)
        self.img = base.convert("RGB")

    def crew(self, keys: list[str], front_x: float, framing: str) -> None:
        """Teammates: smaller, higher in frame, blurred behind the singer."""
        out = 1 if front_x <= 0.5 else -1
        for i, k in enumerate(keys):
            x = front_x - out * (0.2 + 0.13 * i) if framing in ("CU", "ECU") else front_x - out * (0.17 + 0.11 * i)
            x = min(0.95, max(0.05, x))
            self.figure(k, x, framing, scale=0.62, dy=-0.06, blur=9, label=True)

    def overlay(self, fn) -> None:
        layer = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        fn(ImageDraw.Draw(layer))
        base = self.img.convert("RGBA")
        base.alpha_composite(layer)
        self.img = base.convert("RGB")

    def cone(self, cx: float, top_w: float, bottom_w: float, alpha: int = 70) -> None:
        W, H = self.W, self.H

        def draw(d):
            d.polygon([(cx - top_w, 0), (cx + top_w, 0), (cx + bottom_w, 0.9 * H), (cx - bottom_w, 0.9 * H)],
                      fill=(235, 235, 225, alpha))
            d.ellipse([cx - bottom_w * 1.1, 0.86 * H, cx + bottom_w * 1.1, 0.95 * H], fill=(240, 240, 230, alpha + 40))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw(ImageDraw.Draw(layer))
        layer = layer.filter(ImageFilter.GaussianBlur(14 * self.S))
        base = self.img.convert("RGBA")
        base.alpha_composite(layer)
        self.img = base.convert("RGB")

    # ------------------------------------------------------------ stagings

    def draw(self) -> Image.Image:
        s, ep = self.shot, self.ep
        st = s.staging or {"crowd": "crowd_ws", "establish": "high_ws"}.get(s.kind, "")
        fr = s.framing
        who = list(s.who)
        singer = s.singer if s.singer in who else None
        W, H = self.W, self.H
        if st == "blackout_spot":
            self.img = Image.new("RGB", (W, H), (0, 0, 0))
            self.cone(W / 2, 0.02 * W, 0.11 * W)
            for k in who[:1]:
                self.figure(k, 0.5, "WS", scale=2.4, dy=0.02, dark=True)
        elif st == "empty_stage_ws":
            self.img = Image.new("RGB", (W, H), (2, 2, 3))
            self.overlay(lambda d: self.taiji(d, W / 2, 0.84 * H, 0.42 * W, 0.12 * H, (40, 40, 44)))
            self.cone(W / 2, 0.015 * W, 0.08 * W, 45)
        elif st in ("head_down_cu", "spot_cu"):
            self.img = Image.new("RGB", (W, H), (0, 0, 0))
            self.cone(W / 2, 0.05 * W, 0.2 * W, 55)
            for k in who[:1]:
                self.figure(k, 0.5, fr, head_down=st == "head_down_cu")
        elif st == "split_entrance":
            rs = ep.rappers()
            halves = []
            for i, r in enumerate(rs):
                p = _Plate(ep, s, (W // 2, H))
                p.rnd = random.Random(i)
                p.arena(2, 0.6)
                team = [k for k in [r, *ep.team(r)] if not who or k in who]
                xs = [0.5, 0.25, 0.75, 0.12, 0.88]
                for j, k in enumerate(team[1:], 1):
                    p.figure(k, xs[j % len(xs)], "MWS", scale=0.85, dy=0.02)
                p.figure(team[0] if team else r, 0.5, "MWS", dy=0.04)
                halves.append(p.img)
            self.img = Image.new("RGB", (W, H), (0, 0, 0))
            for i, im in enumerate(halves):
                self.img.paste(im, (i * (W // 2), 0))
            self.overlay(lambda d: d.rectangle([W / 2 - 3 * self.S, 0, W / 2 + 3 * self.S, H], fill=(255, 255, 255, 255)))
        elif st == "judge_react":
            self.arena(BLUR.get(fr, 6), 0.7, floor=False)
            judges = [k for k in who if k in ep.cast] + [k for k in ep.members("judge") if k not in who]
            seats = [0.5, 0.12, 0.88]

            def thrones(d):
                for x in seats:
                    cx = x * W
                    d.rectangle([cx - 0.11 * W, 0.08 * H, cx + 0.11 * W, H], fill=(48, 26, 18, 255))
                    d.rectangle([cx - 0.095 * W, 0.12 * H, cx + 0.095 * W, H], fill=(70, 38, 24, 255))
            self.overlay(thrones)
            for k, x in zip(judges[:3], seats):
                self.figure(k, x, fr, blur=0 if k in who else 7)
        elif st in ("dj_booth", "dj_cu"):
            self.arena(BLUR.get(fr, 6), 0.7, floor=False)
            xs = [0.38, 0.62] if len(who) > 1 else [0.5]
            for k, x in zip(who, xs):
                self.figure(k, x, fr)

            def booth(d):
                top = 0.66 * H if st == "dj_booth" else 0.8 * H
                d.rectangle([0.12 * W, top, 0.88 * W, H], fill=(22, 22, 26, 255), outline=(255, 40, 50, 255),
                            width=max(2, int(4 * self.S)))
                for cx in (0.3 * W, 0.7 * W):
                    rr = 0.07 * H
                    d.ellipse([cx - rr * 1.6, top + 0.03 * H, cx + rr * 1.6, top + 0.03 * H + rr], outline=(150, 150, 160, 255),
                              width=max(1, int(3 * self.S)))
            self.overlay(booth)
        elif st == "hook_mic":
            self.arena(BLUR.get(fr, 6))
            k = who[0] if who else None
            if k:
                self.figure(k, 0.5, fr)
            r, hy = FIG.get(fr, FIG["MCU"])
            self.overlay(lambda d: (d.line([(0.5 * W, (hy + r * 0.9) * H), (0.5 * W, H)], fill=(190, 190, 200, 255),
                                           width=max(3, int(8 * self.S))),
                                    d.ellipse([0.5 * W - 0.025 * H, (hy + r * 0.75) * H, 0.5 * W + 0.025 * H,
                                               (hy + r * 0.75) * H + 0.06 * H], fill=(120, 120, 130, 255))))
        elif st == "faceoff_profile":
            self.arena(BLUR.get(fr, 4))
            rs = [k for k in ep.rappers() if k in who] or who
            for k in rs:
                x = 0.40 if ep.cast[k].side == "left" else 0.60
                self.figure(k, x, "MCU", scale=1.15)
            self.overlay(lambda d: d.ellipse([0.485 * W, 0.5 * H, 0.515 * W, 0.58 * H], fill=(200, 200, 210, 255)))
        elif st == "ots_hair":
            self.arena(BLUR.get(fr, 8))
            front = singer or (who[-1] if who else None)
            rival = next((k for k in who if k != front), None)
            fx = _x_of(ep, front) + (0.08 if _x_of(ep, front) > 0.5 else -0.08) if front else 0.6
            if front:
                self.crew(s.background, fx, fr)
                self.figure(front, fx, fr)
            if rival:
                rx = 0.08 if fx > 0.5 else 0.92
                self.figure(rival, rx, "ECU", scale=1.1, dy=0.02, blur=22, label=False)
        elif st in ("crowd_ws", "high_ws", "mic_to_crowd", "cameo_react"):
            many = st in ("crowd_ws", "cameo_react")
            self.arena(BLUR.get(fr, 2), 3.0 if many else 1.2, floor=st != "crowd_ws")
            if many:
                for _ in range(40):  # heads of the audience
                    x, y = self.rnd.uniform(0, W), self.rnd.uniform(0.55 * H, 1.0 * H)
                    r = self.rnd.uniform(0.03, 0.06) * H
                    self.overlay(lambda d, x=x, y=y, r=r: d.ellipse([x - r, y - r, x + r, y + r],
                                                                     fill=(30, 22, 24, 255)))
            if st == "high_ws":
                for k in ep.rappers():
                    self.figure(k, 0.42 if ep.cast[k].side == "left" else 0.58, "WS", dy=0.18)
            for k in who:
                x = _x_of(ep, k) if st != "cameo_react" else 0.5
                self.figure(k, x, fr)
        else:  # cu_team_bg, two_shot, point_lens, mic_to_lens, reactions, entrance / outro defaults
            self.arena(BLUR.get(fr, 6))
            if fr in ("2S", "WS", "MWS") or len(who) > 1:
                n = len(who)
                for i, k in enumerate(who):
                    x = _x_of(ep, k) if k in ep.rappers() else (i + 1) / (n + 1)
                    self.figure(k, x, fr if fr != "WS" else "MWS")
            elif who:
                k = who[0]
                x = _x_of(ep, k)
                x = 0.5 + (x - 0.5) * 0.7
                self.crew(s.background, x, fr)
                self.figure(k, x, fr)
                if st in ("point_lens", "mic_to_lens"):
                    r, hy = FIG.get(fr, FIG["MCU"])
                    self.overlay(lambda d: d.ellipse([x * W - 0.09 * H, (hy + 0.25) * H, x * W + 0.09 * H, (hy + 0.43) * H],
                                                     fill=colour(ep, k) + (255,)))
        self.label()
        return self.img

    def label(self) -> None:
        s, S = self.shot, self.S
        st = cinema.SHOW_STAGINGS.get(s.staging)
        text = f"{s.id} · {st.cn if st else s.kind} · {s.framing} · {s.camera}"

        def draw(d):
            f = _font("sans", int(28 * S), "Bold")
            while d.textlength(text, font=f) > self.W * 0.78 and f.size > 10:
                f = _font("sans", f.size - 2, "Bold")
            # inset so the animated camera move (up to ~14 % zoom) never crops it
            x0, y0 = 0.08 * self.W, 0.08 * self.H
            d.rectangle([x0, y0, x0 + d.textlength(text, font=f) + 40 * S, y0 + 52 * S], fill=(0, 0, 0, 150))
            d.text((x0 + 20 * S, y0 + 36 * S), text, font=f, fill=(255, 255, 255, 235), anchor="ls")
            fw = _font("sans", int(64 * S), "Black")
            d.text((self.W / 2, self.H * 0.22), "PREVIZ 占位", font=fw, fill=(255, 255, 255, 60), anchor="mm")
        self.overlay(draw)


def shot_plate(ep: Episode, shot: BoardShot, size: tuple[int, int], timing: Timing | None = None) -> Image.Image:
    """Placeholder plate for one board shot (RGB, exactly `size`)."""
    return _Plate(ep, shot, size).draw()


def contact_sheets(ep: Episode, shots: list[BoardShot], out_dir: Path, per_sheet: int = 12,
                   thumb: tuple[int, int] = (480, 270)) -> list[Path]:
    """Review grids of the previz plates (edit/previz/sheet_NN.png)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = 3
    paths = []
    for si in range(0, len(shots), per_sheet):
        chunk = shots[si: si + per_sheet]
        rows = math.ceil(len(chunk) / cols)
        sheet = Image.new("RGB", (cols * thumb[0], rows * (thumb[1] + 30)), (16, 16, 18))
        d = ImageDraw.Draw(sheet)
        f = _font("sans", 18, "Bold")
        for i, s in enumerate(chunk):
            x, y = (i % cols) * thumb[0], (i // cols) * (thumb[1] + 30)
            sheet.paste(shot_plate(ep, s, thumb), (x, y))
            d.text((x + 8, y + thumb[1] + 22), f"{s.t0:.2f}-{s.t1:.2f}s · {s.section} · {s.kind}", font=f,
                   fill=(220, 220, 220), anchor="ls")
        p = out_dir / f"sheet_{si // per_sheet + 1:02d}.png"
        sheet.save(p)
        paths.append(p)
    return paths
