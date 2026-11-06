# -*- coding: utf-8 -*-
"""개추 트래스 — Korean-first cinematic episode board.
Upload any number of pictures from Downloads; compose them as a widescreen episode.
©2026 EX Inc./HYPERION DIGITAL ©2026"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, tempfile, threading, time, urllib.request, webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

APP = "개추 트래스"
APP_VERSION = "1.0.0"
COPYRIGHT = "\u00a92026 EX Inc./HYPERION DIGITAL \u00a92026"
REPO = "Teobokki/gaechu-trass"
UPDATE_URL = "https://raw.githubusercontent.com/%s/main/latest.json" % REPO
CATALOG_ID = "gaechu-trass"

BG, PANEL, CARD, CARD2, BORDER = "#0b0b0d", "#121216", "#18181d", "#24242b", "#2c2c34"
TXT, MUT, DIM = "#f2f2f4", "#9a9aa6", "#5d5d66"
RED, RED2, GREEN, AMBER = "#FF4545", "#ff6a6a", "#3ddc84", "#ffb020"
LETTER = (0, 0, 0)
BOARD_RGB = (24, 24, 29)
FONT_UI = "Noto Sans KR"
FONT_MIX = "Noto Sans CJK KR"
FALLBACK_UI = ("Malgun Gothic", "Yu Gothic UI", "Segoe UI", "Arial")

FPS = 24
SCENE_SECS = 4.0
TITLE_SECS = 3.0
END_SECS = 2.5
XFADE_SECS = 0.55
OUT_W, OUT_H = 1280, 720
ZOOM_END = 1.12

IMG_TYPES = [("이미지", "*.png *.jpg *.jpeg *.webp *.gif *.bmp"), ("모든 파일", "*.*")]

if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageTk


def res_path(*n):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *n)


def downloads_dir():
    d = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            class GUID(ctypes.Structure):
                _fields_ = [("a", wintypes.DWORD), ("b", wintypes.WORD), ("c", wintypes.WORD), ("d", ctypes.c_ubyte * 8)]
            g = GUID(0x374DE290, 0x123F, 0x4565, (ctypes.c_ubyte * 8)(0x91, 0x64, 0x39, 0xC4, 0x92, 0x5E, 0x46, 0x7B))
            p = ctypes.c_wchar_p()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(g), 0, None, ctypes.byref(p)) == 0 and p.value:
                d = p.value
        except Exception:
            pass
    os.makedirs(d, exist_ok=True)
    return d


def register_fonts():
    """Register bundled CJK fonts with Windows GDI so Tk and the shell can use them."""
    names = []
    if os.name == "nt":
        try:
            import ctypes
            for fn in ("NotoSansKR-Regular.otf", "NotoSansKR-Bold.otf", "NotoSansCJKkr-Regular.otf"):
                path = res_path("fonts", fn)
                if os.path.isfile(path):
                    ctypes.windll.gdi32.AddFontResourceExW(path, 0x10, 0)
                    names.append(path)
        except Exception:
            pass
    return names


def pick_family(preferred, families):
    for name in preferred:
        if name in families:
            return name
    return preferred[0]


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", str(v))[:4]) or (0,)


def check_update():
    try:
        req = urllib.request.Request(UPDATE_URL + "?t=%d" % time.time(),
                                     headers={"User-Agent": "GAECHU-TRASS/" + APP_VERSION})
        with urllib.request.urlopen(req, timeout=10) as r:
            m = json.loads(r.read(65536).decode("utf-8"))
        ver = str(m["version"])
    except Exception as e:
        return "error", "업데이트를 확인하지 못했습니다 (%s)." % (getattr(e, "reason", None) or e)
    if vtuple(ver) > vtuple(APP_VERSION):
        return "newer", {"version": ver, "notes": str(m.get("notes", "")),
                         "link": str(m.get("installer_url") or m.get("url", ""))}
    return "latest", "최신 버전입니다 (%s)." % APP_VERSION


def ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or "ffmpeg"


def open_image_rgb(path, max_side=2048):
    im = Image.open(path)
    try:
        im.seek(0)
    except Exception:
        pass
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA", "P", "PA"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, BOARD_RGB + (255,))
        im = Image.alpha_composite(bg, im)
    im = im.convert("RGB")
    if max(im.size) > max_side:
        im.thumbnail((max_side, max_side), Image.LANCZOS)
    return im


def trash_icon(color=(242, 242, 244), size=16):
    from PIL import ImageDraw as ID
    k = 8
    S = size * k
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ID.Draw(im)
    c = tuple(color) + (255,)
    d.rounded_rectangle([S * .38, S * .04, S * .62, S * .16], radius=S * .04, outline=c, width=int(S * .07))
    d.rounded_rectangle([S * .10, S * .14, S * .90, S * .24], radius=S * .04, fill=c)
    d.polygon([(S * .18, S * .30), (S * .82, S * .30), (S * .75, S * .96), (S * .25, S * .96)], fill=c)
    for x in (.37, .50, .63):
        d.rounded_rectangle([S * (x - .035), S * .40, S * (x + .035), S * .86], radius=S * .03, fill=(0, 0, 0, 0))
    return ImageTk.PhotoImage(im.resize((size, size), Image.LANCZOS))


class Btn(tk.Label):
    def __init__(self, master, text, cmd, fill=CARD2, fg=TXT, hover=None, **kw):
        super().__init__(master, text=text, bg=fill, fg=fg, font=kw.pop("font", (FONT_UI, 10, "bold")),
                         cursor="hand2", padx=kw.pop("padx", 14), pady=kw.pop("pady", 7), **kw)
        self.fill, self.hover, self.cmd, self.enabled, self.fg0 = fill, hover or BORDER, cmd, True, fg
        self.bind("<Button-1>", lambda e: self.enabled and self.cmd())
        self.bind("<Enter>", lambda e: self.enabled and self.configure(bg=self.hover))
        self.bind("<Leave>", lambda e: self.configure(bg=self.fill))

    def set_enabled(self, on):
        self.enabled = on
        self.configure(fg=self.fg0 if on else DIM, cursor="hand2" if on else "arrow")


# -------------------- fonts for Pillow episode cards --------------------
_font_cache = {}


def pil_font(size, bold=False, mixed=False):
    key = (size, bold, mixed)
    if key in _font_cache:
        return _font_cache[key]
    candidates = []
    if mixed:
        candidates.append(res_path("fonts", "NotoSansCJKkr-Regular.otf"))
    if bold:
        candidates.append(res_path("fonts", "NotoSansKR-Bold.otf"))
    candidates += [
        res_path("fonts", "NotoSansKR-Regular.otf"),
        res_path("fonts", "NotoSansCJKkr-Regular.otf"),
    ]
    font = None
    for p in candidates:
        if os.path.isfile(p):
            try:
                font = ImageFont.truetype(p, size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()
    _font_cache[key] = font
    return font


def fit_cover(im, tw, th, zoom=1.0, pan=(0.5, 0.5)):
    """Scale image to cover tw x th, then crop with pan (0..1) and zoom (>=1)."""
    zoom = max(1.0, float(zoom))
    iw, ih = im.size
    scale = max(tw / iw, th / ih) * zoom
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    resized = im.resize((nw, nh), Image.LANCZOS)
    cx = pan[0] * nw
    cy = pan[1] * nh
    left = int(cx - tw / 2)
    top = int(cy - th / 2)
    left = max(0, min(left, nw - tw))
    top = max(0, min(top, nh - th))
    return resized.crop((left, top, left + tw, top + th))


def letterbox_frame(inner, tw=OUT_W, th=OUT_H, bar=0.0):
    """Place inner RGB onto black 16:9; bar unused (inner already sized)."""
    if inner.size == (tw, th):
        return inner
    out = Image.new("RGB", (tw, th), LETTER)
    iw, ih = inner.size
    scale = min(tw / iw, th / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    r = inner.resize((nw, nh), Image.LANCZOS)
    out.paste(r, ((tw - nw) // 2, (th - nh) // 2))
    return out


def make_title_card(title, subtitle=None, tw=OUT_W, th=OUT_H):
    im = Image.new("RGB", (tw, th), (8, 10, 16))
    d = ImageDraw.Draw(im)
    # soft vignette bars
    d.rectangle([0, 0, tw, int(th * 0.12)], fill=(0, 0, 0))
    d.rectangle([0, int(th * 0.88), tw, th], fill=(0, 0, 0))
    brand = pil_font(max(28, th // 18), bold=True, mixed=True)
    title_f = pil_font(max(36, th // 12), bold=True, mixed=True)
    sub_f = pil_font(max(18, th // 28), bold=False, mixed=True)
    d.text((tw / 2, th * 0.32), APP, font=brand, fill=(120, 160, 210), anchor="mm")
    text = (title or "에피소드").strip() or "에피소드"
    d.text((tw / 2, th * 0.50), text, font=title_f, fill=(242, 242, 244), anchor="mm")
    if subtitle:
        d.text((tw / 2, th * 0.62), subtitle, font=sub_f, fill=(154, 154, 166), anchor="mm")
    d.text((tw / 2, th * 0.90), COPYRIGHT, font=sub_f, fill=(70, 70, 80), anchor="mm")
    return im


def make_end_card(title, tw=OUT_W, th=OUT_H):
    im = Image.new("RGB", (tw, th), (8, 10, 16))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, tw, int(th * 0.12)], fill=(0, 0, 0))
    d.rectangle([0, int(th * 0.88), tw, th], fill=(0, 0, 0))
    f1 = pil_font(max(34, th // 14), bold=True, mixed=True)
    f2 = pil_font(max(18, th // 28), bold=False, mixed=True)
    d.text((tw / 2, th * 0.42), "끝", font=f1, fill=(242, 242, 244), anchor="mm")
    d.text((tw / 2, th * 0.55), (title or APP).strip() or APP, font=f2, fill=(154, 154, 166), anchor="mm")
    d.text((tw / 2, th * 0.90), COPYRIGHT, font=f2, fill=(70, 70, 80), anchor="mm")
    return im


def scene_pan_for_index(i):
    """Vary pan direction per scene so motion feels intentional."""
    patterns = [
        ((0.42, 0.50), (0.58, 0.50)),  # left -> right
        ((0.50, 0.42), (0.50, 0.58)),  # up -> down
        ((0.58, 0.50), (0.42, 0.50)),  # right -> left
        ((0.50, 0.58), (0.50, 0.42)),  # down -> up
        ((0.45, 0.45), (0.55, 0.55)),  # diagonal
    ]
    return patterns[i % len(patterns)]


def lerp(a, b, t):
    return a + (b - a) * t


def blend(a, b, t):
    if t <= 0:
        return a
    if t >= 1:
        return b
    return Image.blend(a, b, t)


class EpisodeComposer:
    """Builds the timeline of RGB frames for preview/export."""

    def __init__(self, scenes, title):
        self.scenes = scenes  # list of PIL RGB images
        self.title = title or "에피소드"

    def timeline(self):
        """Yield (global_t_end, kind, payload) segments — used by renderer."""
        segs = []
        t = 0.0
        segs.append((TITLE_SECS, "title", None))
        t += TITLE_SECS
        for i, im in enumerate(self.scenes):
            segs.append((SCENE_SECS, "scene", (i, im)))
            t += SCENE_SECS
        segs.append((END_SECS, "end", None))
        return segs

    def total_seconds(self):
        n = len(self.scenes)
        return TITLE_SECS + n * SCENE_SECS + END_SECS

    def frame_at(self, t):
        """Return a finished 16:9 RGB frame at time t (seconds)."""
        if t < TITLE_SECS:
            return make_title_card(self.title)
        t2 = t - TITLE_SECS
        n = len(self.scenes)
        if n == 0:
            return make_end_card(self.title)
        scene_span = SCENE_SECS
        total_scenes = n * scene_span
        if t2 < total_scenes:
            idx = min(n - 1, int(t2 / scene_span))
            local = t2 - idx * scene_span
            progress = max(0.0, min(1.0, local / scene_span))
            pan0, pan1 = scene_pan_for_index(idx)
            pan = (lerp(pan0[0], pan1[0], progress), lerp(pan0[1], pan1[1], progress))
            zoom = lerp(1.0, ZOOM_END, progress)
            fr = fit_cover(self.scenes[idx], OUT_W, OUT_H, zoom=zoom, pan=pan)
            # crossfade into next near end of scene
            if local >= scene_span - XFADE_SECS and idx + 1 < n:
                fade = (local - (scene_span - XFADE_SECS)) / XFADE_SECS
                pan0b, pan1b = scene_pan_for_index(idx + 1)
                fr2 = fit_cover(self.scenes[idx + 1], OUT_W, OUT_H, zoom=1.0, pan=pan0b)
                fr = blend(fr, fr2, fade)
            elif local >= scene_span - XFADE_SECS and idx + 1 >= n:
                fade = (local - (scene_span - XFADE_SECS)) / XFADE_SECS
                fr = blend(fr, make_end_card(self.title), fade)
            return fr
        return make_end_card(self.title)


def export_episode(scenes, title, out_path, progress=None):
    comp = EpisodeComposer(scenes, title)
    total = comp.total_seconds()
    nframes = max(1, int(total * FPS))
    ff = ffmpeg_exe()
    cmd = [
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (OUT_W, OUT_H),
        "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "20",
        "-movflags", "+faststart", out_path,
    ]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        raise RuntimeError("인코더를 시작하지 못했습니다: %s" % e)
    err = b""
    try:
        for i in range(nframes):
            t = i / float(FPS)
            fr = comp.frame_at(t)
            if fr.size != (OUT_W, OUT_H):
                fr = fr.resize((OUT_W, OUT_H), Image.LANCZOS)
            proc.stdin.write(fr.tobytes())
            if progress and (i % 4 == 0 or i == nframes - 1):
                progress((i + 1) / nframes)
        proc.stdin.close()
        err = proc.stderr.read() if proc.stderr else b""
        rc = proc.wait(timeout=120)
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        raise RuntimeError(str(e))
    if rc != 0 or not os.path.isfile(out_path) or os.path.getsize(out_path) < 1000:
        raise RuntimeError("영상 내보내기 실패: " + (err.decode("utf-8", "replace")[-400:] if err else "unknown"))
    return out_path


# ------------------------------- App -----------------------------------
class Studio(tk.Tk):
    def __init__(self):
        super().__init__()
        register_fonts()
        self.title(APP)
        self.configure(bg=BG)
        self.geometry("1180x860")
        self.minsize(800, 640)
        try:
            self.iconbitmap(default=res_path("assets", "logo.ico"))
        except Exception:
            pass
        try:
            self._ic = tk.PhotoImage(file=res_path("assets", "icon256.png"))
            self.iconphoto(True, self._ic)
        except Exception:
            pass

        fams = set(tkfont.families(self))
        global FONT_UI, FONT_MIX
        FONT_UI = pick_family((FONT_UI,) + FALLBACK_UI, fams)
        FONT_MIX = pick_family((FONT_MIX, "Noto Sans KR", "Noto Sans CJK KR") + FALLBACK_UI, fams)

        self.scenes = []  # dicts: path, name, im (PIL), thumb (ImageTk)
        self.sel = None
        self.playing = False
        self.play_t0 = 0.0
        self.play_job = None
        self.busy = False
        self.photo = None
        self.strip_photos = []
        self._drag = None
        self.ep_title = tk.StringVar(value="에피소드 1")
        self._style()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(200, self._draw_empty)
        self._setup_drop()

    def _style(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except Exception:
            pass
        st.configure("red.Horizontal.TProgressbar", troughcolor=CARD2, background=RED,
                     bordercolor=CARD2, lightcolor=RED, darkcolor=RED)

    def _build(self):
        top = tk.Frame(self, bg=PANEL)
        top.pack(fill="x")
        try:
            lg = Image.open(res_path("assets", "logo64.png")).resize((34, 34), Image.LANCZOS)
            self._logo = ImageTk.PhotoImage(lg)
            tk.Label(top, image=self._logo, bg=PANEL).pack(side="left", padx=(16, 8), pady=10)
        except Exception:
            pass
        tk.Label(top, text=APP, bg=PANEL, fg=TXT, font=(FONT_UI, 15, "bold")).pack(side="left")
        tk.Label(top, text="  v" + APP_VERSION, bg=PANEL, fg=MUT, font=(FONT_UI, 9)).pack(side="left", pady=(6, 0))
        Btn(top, "↺  업데이트 확인", self.check_updates, fill=PANEL, fg=MUT, hover=CARD2,
            font=(FONT_UI, 9, "bold")).pack(side="right", padx=12)

        nav = tk.Frame(top, bg=PANEL)
        nav.pack(side="left", padx=(28, 0), fill="y")
        f = tk.Frame(nav, bg=PANEL)
        f.pack(side="left", padx=2, fill="y")
        l = tk.Label(f, text="⌂  보드", bg=PANEL, fg=TXT, font=(FONT_UI, 10, "bold"), padx=14, pady=8)
        l.pack(side="top", fill="y", expand=True)
        tk.Frame(f, bg=RED, height=3).pack(side="bottom", fill="x")

        tk.Label(self, text=COPYRIGHT, bg=PANEL, fg=DIM, font=(FONT_UI, 8), pady=3).pack(side="bottom", fill="x")

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)

        bar = tk.Frame(self.body, bg=BG)
        bar.pack(fill="x", padx=16, pady=(12, 8))
        Btn(bar, "⬆  이미지 추가", self.add_images, fill=RED, fg="white", hover=RED2).pack(side="left")
        self.b_play = Btn(bar, "▶  재생", self.play)
        self.b_play.pack(side="left", padx=(8, 0))
        self.b_stop = Btn(bar, "■  정지", self.stop)
        self.b_stop.pack(side="left", padx=(8, 0))

        tk.Label(bar, text="에피소드 제목", bg=BG, fg=MUT, font=(FONT_UI, 9, "bold")).pack(side="left", padx=(18, 6))
        self.title_entry = tk.Entry(bar, textvariable=self.ep_title, bg=CARD, fg=TXT, insertbackground=RED,
                                    relief="flat", font=(FONT_MIX, 11), width=28,
                                    highlightthickness=1, highlightbackground=BORDER, highlightcolor=RED)
        self.title_entry.pack(side="left", ipady=5)

        self.b_export = Btn(bar, "⬇  내보내기", self.export, fill=CARD2)
        self.b_export.pack(side="right")
        self._trash = trash_icon()
        self.b_bin = Btn(bar, " 비우기", self.clear_all, fill=CARD2, hover="#5a1f1f",
                         image=self._trash, compound="left")
        self.b_bin.pack(side="right", padx=(0, 8))

        # status
        stat = tk.Frame(self.body, bg=BG)
        stat.pack(side="bottom", fill="x", padx=16, pady=(0, 6))
        self.status = tk.Label(stat, text="다운로드에서 그림이나 사진을 올려 시작하세요.", bg=BG, fg=MUT,
                               font=(FONT_UI, 9), anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        self.prog = ttk.Progressbar(stat, style="red.Horizontal.TProgressbar", length=180,
                                    mode="determinate", maximum=1.0)

        # scene strip
        strip_wrap = tk.Frame(self.body, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        strip_wrap.pack(side="bottom", fill="x", padx=16, pady=(0, 8))
        head = tk.Frame(strip_wrap, bg=PANEL)
        head.pack(fill="x", padx=10, pady=(8, 0))
        tk.Label(head, text="장면", bg=PANEL, fg=MUT, font=(FONT_UI, 8, "bold")).pack(side="left")
        Btn(head, "삭제", self.remove_selected, fill=PANEL, fg=MUT, hover=CARD2,
            font=(FONT_UI, 8, "bold"), padx=8, pady=2).pack(side="right")
        Btn(head, "아래로", self.move_down, fill=PANEL, fg=MUT, hover=CARD2,
            font=(FONT_UI, 8, "bold"), padx=8, pady=2).pack(side="right")
        Btn(head, "위로", self.move_up, fill=PANEL, fg=MUT, hover=CARD2,
            font=(FONT_UI, 8, "bold"), padx=8, pady=2).pack(side="right")

        self.strip_canvas = tk.Canvas(strip_wrap, bg=CARD, height=96, highlightthickness=0, cursor="hand2")
        self.strip_scroll = ttk.Scrollbar(strip_wrap, orient="horizontal", command=self.strip_canvas.xview)
        self.strip_canvas.configure(xscrollcommand=self.strip_scroll.set)
        self.strip_canvas.pack(fill="x", padx=8, pady=(4, 0))
        self.strip_scroll.pack(fill="x", padx=8, pady=(0, 8))
        self.strip_inner = tk.Frame(self.strip_canvas, bg=CARD)
        self.strip_win = self.strip_canvas.create_window((0, 0), window=self.strip_inner, anchor="nw")
        self.strip_inner.bind("<Configure>", lambda e: self.strip_canvas.configure(
            scrollregion=self.strip_canvas.bbox("all")))

        # main board
        board = tk.Frame(self.body, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
        board.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.canvas = tk.Canvas(board, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._on_resize())
        self.canvas.bind("<Button-1>", lambda e: self.add_images() if not self.scenes else None)

    def _setup_drop(self):
        """Best-effort drag-and-drop of image files onto the board (Windows)."""
        if os.name != "nt":
            return
        try:
            import windnd
            def _dropped(files):
                paths = []
                for f in files:
                    if isinstance(f, bytes):
                        try:
                            f = f.decode("utf-8")
                        except Exception:
                            f = f.decode("mbcs", "replace")
                    paths.append(f)
                self.after(0, lambda: self._add_paths(paths))
            windnd.hook_dropfiles(self.canvas, func=_dropped)
        except Exception:
            pass

    def set_status(self, t, color=MUT):
        self.status.configure(text=t, fg=color)

    def _busy(self, on):
        self.busy = on
        for b in (self.b_play, self.b_export, self.b_bin):
            b.set_enabled(not on)

    def _draw_empty(self):
        cv = self.canvas
        cv.delete("all")
        cw, ch = max(1, cv.winfo_width()), max(1, cv.winfo_height())
        # letterbox preview area
        target_aspect = 16 / 9
        if cw / ch > target_aspect:
            bh = ch
            bw = int(ch * target_aspect)
        else:
            bw = cw
            bh = int(cw / target_aspect)
        x0, y0 = (cw - bw) // 2, (ch - bh) // 2
        cv.create_rectangle(x0, y0, x0 + bw, y0 + bh, fill="#0a0a0c", outline="")
        try:
            lg = Image.open(res_path("assets", "icon256.png")).resize((72, 72), Image.LANCZOS)
            self._empty_logo = ImageTk.PhotoImage(lg)
            cv.create_image(cw / 2, ch / 2 - 36, image=self._empty_logo)
        except Exception:
            pass
        cv.create_text(cw / 2, ch / 2 + 40, text=APP, fill=TXT, font=(FONT_UI, 16, "bold"))
        cv.create_text(cw / 2, ch / 2 + 70,
                       text="다운로드에서 그림이나 사진을 올려 시작하세요.",
                       fill=MUT, font=(FONT_UI, 11))
        cv.create_text(cw / 2, ch / 2 + 96,
                       text="이미지 수 제한 없음 · 장면 순서로 에피소드가 만들어집니다",
                       fill=DIM, font=(FONT_UI, 9))

    def _on_resize(self):
        if self.playing:
            return
        if not self.scenes:
            self._draw_empty()
        else:
            self._show_still(0)

    def _show_pil(self, im):
        cv = self.canvas
        cw, ch = max(1, cv.winfo_width()), max(1, cv.winfo_height())
        # fit 16:9 image into canvas with letterbox
        frame = Image.new("RGB", (cw, ch), (0, 0, 0))
        scale = min(cw / im.width, ch / im.height)
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        r = im.resize((nw, nh), Image.BILINEAR)
        frame.paste(r, ((cw - nw) // 2, (ch - nh) // 2))
        self.photo = ImageTk.PhotoImage(frame)
        cv.delete("all")
        cv.create_image(0, 0, image=self.photo, anchor="nw")

    def _show_still(self, idx):
        if not self.scenes:
            self._draw_empty()
            return
        idx = max(0, min(idx, len(self.scenes) - 1))
        im = fit_cover(self.scenes[idx]["im"], OUT_W, OUT_H, zoom=1.0, pan=(0.5, 0.5))
        self._show_pil(im)

    def add_images(self):
        if self.busy or self.playing:
            return
        paths = filedialog.askopenfilenames(
            parent=self, title="이미지 추가", initialdir=downloads_dir(),
            filetypes=IMG_TYPES)
        if paths:
            self._add_paths(list(paths))

    def _add_paths(self, paths):
        added = 0
        for p in paths:
            if not p or not os.path.isfile(p):
                continue
            ext = os.path.splitext(p)[1].lower()
            if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"):
                continue
            try:
                im = open_image_rgb(p)
            except Exception as e:
                self.set_status("불러오기 실패: %s (%s)" % (os.path.basename(p), e), RED2)
                continue
            thumb = im.copy()
            thumb.thumbnail((120, 72), Image.LANCZOS)
            # pad thumb to 120x72
            pad = Image.new("RGB", (120, 72), BOARD_RGB)
            pad.paste(thumb, ((120 - thumb.width) // 2, (72 - thumb.height) // 2))
            tk_thumb = ImageTk.PhotoImage(pad)
            self.scenes.append({
                "path": p, "name": os.path.basename(p), "im": im, "thumb": tk_thumb,
            })
            added += 1
        if added:
            self.sel = len(self.scenes) - 1
            self._refresh_strip()
            self._show_still(self.sel)
            self.set_status("%d장 추가됨 · 장면 %d장" % (added, len(self.scenes)), GREEN)

    def _refresh_strip(self):
        for w in self.strip_inner.winfo_children():
            w.destroy()
        self.strip_photos = []
        for i, sc in enumerate(self.scenes):
            cell = tk.Frame(self.strip_inner, bg=RED if i == self.sel else CARD2,
                            highlightthickness=0, padx=2, pady=2)
            cell.pack(side="left", padx=4, pady=4)
            lbl = tk.Label(cell, image=sc["thumb"], bg=CARD, cursor="hand2")
            lbl.pack()
            cap = tk.Label(cell, text="%d" % (i + 1), bg=cell["bg"], fg=TXT,
                           font=(FONT_UI, 8, "bold"))
            cap.pack()
            for w in (cell, lbl, cap):
                w.bind("<Button-1>", lambda e, idx=i: self._select(idx))
                w.bind("<Double-Button-1>", lambda e, idx=i: self._show_still(idx))
            self.strip_photos.append(sc["thumb"])

    def _select(self, idx):
        self.sel = idx
        self._refresh_strip()
        if not self.playing:
            self._show_still(idx)

    def remove_selected(self):
        if self.busy or self.playing or self.sel is None or not self.scenes:
            return
        del self.scenes[self.sel]
        if not self.scenes:
            self.sel = None
            self._refresh_strip()
            self._draw_empty()
            self.set_status("다운로드에서 그림이나 사진을 올려 시작하세요.", MUT)
            return
        self.sel = min(self.sel, len(self.scenes) - 1)
        self._refresh_strip()
        self._show_still(self.sel)
        self.set_status("장면 삭제됨 · %d장" % len(self.scenes), MUT)

    def move_up(self):
        if self.sel is None or self.sel <= 0 or self.playing:
            return
        i = self.sel
        self.scenes[i - 1], self.scenes[i] = self.scenes[i], self.scenes[i - 1]
        self.sel = i - 1
        self._refresh_strip()
        self._show_still(self.sel)

    def move_down(self):
        if self.sel is None or self.sel >= len(self.scenes) - 1 or self.playing:
            return
        i = self.sel
        self.scenes[i + 1], self.scenes[i] = self.scenes[i], self.scenes[i + 1]
        self.sel = i + 1
        self._refresh_strip()
        self._show_still(self.sel)

    def clear_all(self):
        if self.busy:
            return
        self.stop()
        if self.scenes and not messagebox.askyesno(APP, "보드의 모든 장면을 지울까요?", parent=self):
            return
        self.scenes.clear()
        self.sel = None
        self._refresh_strip()
        self._draw_empty()
        self.set_status("보드를 비웠습니다. 다운로드에서 그림이나 사진을 올려 시작하세요.", MUT)

    def play(self):
        if self.busy:
            return
        if not self.scenes:
            messagebox.showinfo(APP, "먼저 이미지를 추가하세요.", parent=self)
            return
        self.stop()
        self.playing = True
        self.play_t0 = time.time()
        imgs = [s["im"] for s in self.scenes]
        self._composer = EpisodeComposer(imgs, self.ep_title.get())
        self.set_status("재생 중…", GREEN)
        self._tick()

    def _tick(self):
        if not self.playing:
            return
        t = time.time() - self.play_t0
        total = self._composer.total_seconds()
        if t >= total:
            self._show_pil(self._composer.frame_at(total - 0.01))
            self.playing = False
            self.set_status("재생 완료. 내보내기로 MP4를 저장할 수 있습니다.", MUT)
            return
        self._show_pil(self._composer.frame_at(t))
        self.play_job = self.after(int(1000 / FPS), self._tick)

    def stop(self):
        self.playing = False
        if self.play_job:
            try:
                self.after_cancel(self.play_job)
            except Exception:
                pass
            self.play_job = None
        if self.scenes:
            self.set_status("정지 · 장면 %d장" % len(self.scenes), MUT)

    def export(self):
        if self.busy:
            return
        if not self.scenes:
            messagebox.showinfo(APP, "먼저 이미지를 추가하세요.", parent=self)
            return
        self.stop()
        title = (self.ep_title.get() or "에피소드").strip() or "에피소드"
        # safe filename
        safe = re.sub(r'[\\/:*?"<>|]+', "_", title)[:60]
        out = os.path.join(downloads_dir(), "%s %s %s.mp4" % (APP, safe, time.strftime("%Y-%m-%d %H-%M-%S")))
        imgs = [s["im"] for s in self.scenes]
        self._busy(True)
        self.prog.pack(side="right", padx=(8, 0))
        self.prog["value"] = 0
        self.set_status("내보내는 중…", TXT)

        def prog(v):
            self.after(0, lambda: (self.prog.configure(value=v),
                                   self.set_status("내보내는 중… %d%%" % int(v * 100), TXT)))

        def work():
            try:
                export_episode(imgs, title, out, progress=prog)
            except Exception as e:
                self.after(0, lambda: self._export_done(None, str(e)))
            else:
                self.after(0, lambda: self._export_done(out, None))

        threading.Thread(target=work, daemon=True).start()

    def _export_done(self, out, err):
        self._busy(False)
        self.prog.pack_forget()
        if err:
            self.set_status("내보내기 실패: " + err, RED2)
            messagebox.showerror(APP, "내보내기 실패:\n" + err, parent=self)
            return
        self.set_status("저장됨: " + out, GREEN)
        try:
            if os.name == "nt":
                os.startfile(os.path.dirname(out))
        except Exception:
            pass

    def check_updates(self):
        self.set_status("업데이트 확인 중…", TXT)

        def work():
            st, d = check_update()
            self.after(0, lambda: self._update_result(st, d))

        threading.Thread(target=work, daemon=True).start()

    def _update_result(self, st, d):
        if st == "error":
            self.set_status(d, MUT)
            return
        if st == "latest":
            self.set_status(d, MUT)
            return
        self.set_status("업데이트 %s 사용 가능." % d["version"], GREEN)
        if d.get("link") and messagebox.askyesno(
                APP, "새 버전 %s이(가) 있습니다.\n\n%s\n\n다운로드 페이지를 열까요?" % (
                    d["version"], d.get("notes") or ""), parent=self):
            webbrowser.open(d["link"])

    def on_close(self):
        self.stop()
        self.destroy()


def main():
    app = Studio()
    app.mainloop()


if __name__ == "__main__":
    main()
