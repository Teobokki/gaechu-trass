# -*- coding: utf-8 -*-
"""개추 트래스 — Korean-first cinematic episode maker.
Episode home for saved works; maker board to compose pictures into a widescreen episode.
©2026 EX Inc./HYPERION DIGITAL ©2026"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, tempfile, threading, time, urllib.request, webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont

APP = "개추 트래스"
APP_VERSION = "1.0.3"
COPYRIGHT = "\u00a92026 EX Inc./HYPERION DIGITAL \u00a92026"
REPO = "Teobokki/gaechu-trass"
UPDATE_URL = "https://raw.githubusercontent.com/%s/main/latest.json" % REPO
CATALOG_ID = "gaechu-trass"

BUNDLED_EPISODE = {
    "id": "bundled-episode-1",
    "title": "개추 트래스",
    "subtitle": "에피소드 1",
    "created": "2026-11-06T00:00:00",
    "bundled": True,
    "mp4_rel": ("assets", "episodes", "episode1.mp4"),
    "poster_rel": ("assets", "episodes", "episode1_poster.jpg"),
}

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


def app_data_dir():
    """Per-user app data: %LOCALAPPDATA%\\개추 트래스 on Windows."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    else:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    d = os.path.join(base, APP)
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "posters"), exist_ok=True)
    return d


def library_path():
    return os.path.join(app_data_dir(), "library.json")


def load_library():
    p = library_path()
    if not os.path.isfile(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        eps = data.get("episodes") if isinstance(data, dict) else None
        return [e for e in (eps or []) if isinstance(e, dict)]
    except Exception:
        return []


def save_library(episodes):
    with open(library_path(), "w", encoding="utf-8") as f:
        json.dump({"version": 1, "episodes": episodes}, f, ensure_ascii=False, indent=2)


def open_media(path):
    """Open a local video with the OS default player."""
    if not path or not os.path.isfile(path):
        return False
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        try:
            webbrowser.open("file:///" + path.replace("\\", "/"))
            return True
        except Exception:
            return False


def episode_paths(ep):
    """Return (mp4_path, poster_path) for a library or bundled episode."""
    if ep.get("bundled"):
        mp4 = res_path(*ep.get("mp4_rel", ("assets", "episodes", "episode1.mp4")))
        poster = res_path(*ep.get("poster_rel", ("assets", "episodes", "episode1_poster.jpg")))
        return mp4, poster
    return ep.get("mp4") or "", ep.get("poster") or ""


def probe_duration(path):
    """Best-effort duration in seconds via ffmpeg -i stderr."""
    try:
        ff = ffmpeg_exe()
        p = subprocess.run([ff, "-i", path], capture_output=True, timeout=20)
        err = (p.stderr or b"").decode("utf-8", "replace")
        m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", err)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    except Exception:
        pass
    return 0.0


def all_episodes():
    """Featured bundled episode first, then user exports (newest first)."""
    out = [dict(BUNDLED_EPISODE)]
    for e in load_library():
        if e.get("id") == BUNDLED_EPISODE["id"] or e.get("bundled"):
            continue
        out.append(e)
    return out



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


# ------------------------- TTS SUBTITLES (optional) -------------------------
# Typed per-scene text is burned in as a caption and narrated. Empty = nothing.
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
TTS_RATE = 48000
TTS_LEAD = 0.30   # silence before a line starts inside its scene
TTS_TAIL = 0.45   # breathing room after the line, before the crossfade
TTS_VOICES = {
    "ko": ("ko-KR-SunHiNeural", "ko-KR"),
    "ja": ("ja-JP-NanamiNeural", "ja-JP"),
    "en": ("en-US-AriaNeural", "en-US"),
}
_HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
_KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f]")
_HAN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_tts_dur_cache = {}


def clean_caption(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def detect_lang(text):
    """Hangul -> ko, kana (or kanji-only) -> ja, else en."""
    if _HANGUL.search(text):
        return "ko"
    if _KANA.search(text) or _HAN.search(text):
        return "ja"
    return "en"


def run_hidden(cmd, timeout=120, **kw):
    return subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=NO_WINDOW, **kw)


def tts_cache_dir():
    d = os.path.join(app_data_dir(), "tts")
    os.makedirs(d, exist_ok=True)
    return d


def _to_wav(src, dst):
    p = run_hidden([ffmpeg_exe(), "-y", "-loglevel", "error", "-i", src,
                    "-ac", "1", "-ar", str(TTS_RATE), "-c:a", "pcm_s16le", dst])
    if p.returncode != 0 or not os.path.isfile(dst) or os.path.getsize(dst) < 200:
        raise RuntimeError((p.stderr or b"").decode("utf-8", "replace")[-200:] or "wav convert failed")
    return dst


def _tts_edge(text, voice, mp3):
    import asyncio
    import edge_tts

    async def go():
        await edge_tts.Communicate(text, voice).save(mp3)
    asyncio.run(go())
    if not os.path.isfile(mp3) or os.path.getsize(mp3) < 200:
        raise RuntimeError("edge-tts returned no audio")


def _tts_sapi(text, culture, wav):
    """Offline Windows voices (e.g. Microsoft Heami on Korean Windows) via System.Speech."""
    if os.name != "nt":
        raise RuntimeError("Windows voice not available")
    txt = wav + ".txt"
    with open(txt, "w", encoding="utf-8-sig") as f:
        f.write(text)
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        "$c='%s';"
        "$v=$s.GetInstalledVoices()|?{$_.Enabled -and $_.VoiceInfo.Culture.Name -eq $c}|select -First 1;"
        "if(-not $v){$v=$s.GetInstalledVoices()|?{$_.Enabled -and $_.VoiceInfo.Culture.Name.StartsWith($c.Substring(0,2))}|select -First 1};"
        "if($v){$s.SelectVoice($v.VoiceInfo.Name)};"
        "$t=[IO.File]::ReadAllText('%s',[Text.Encoding]::UTF8);"
        "$s.SetOutputToWaveFile('%s');$s.Speak($t);$s.Dispose()"
    ) % (culture, txt.replace("'", "''"), wav.replace("'", "''"))
    try:
        p = run_hidden(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                        "-Command", ps], timeout=180)
    finally:
        try:
            os.remove(txt)
        except Exception:
            pass
    if p.returncode != 0 or not os.path.isfile(wav) or os.path.getsize(wav) < 200:
        raise RuntimeError((p.stderr or b"").decode("utf-8", "replace")[-200:] or "Windows voice failed")


def wav_seconds(path):
    import wave
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate() or 1)


def tts_wav(text):
    """Return (wav_path, seconds, engine) for text; cached per text+voice. Raises if all engines fail."""
    import hashlib
    text = clean_caption(text)
    if not text:
        return None, 0.0, ""
    lang = detect_lang(text)
    voice, culture = TTS_VOICES[lang]
    key = hashlib.sha1(("v1|%s|%s" % (voice, text)).encode("utf-8")).hexdigest()[:20]
    out = os.path.join(tts_cache_dir(), key + ".wav")
    if os.path.isfile(out) and os.path.getsize(out) > 200:
        sec = wav_seconds(out)
        _tts_dur_cache[text] = sec
        return out, sec, "cache"
    errs = []
    tmp_mp3 = out + ".mp3"
    try:
        _tts_edge(text, voice, tmp_mp3)
        _to_wav(tmp_mp3, out)
        engine = "edge:" + voice
    except Exception as e:
        errs.append("online voice: %s" % e)
        engine = ""
    finally:
        try:
            os.remove(tmp_mp3)
        except Exception:
            pass
    if not engine:
        raw = out + ".sapi.wav"
        try:
            _tts_sapi(text, culture, raw)
            _to_wav(raw, out)
            engine = "windows:" + culture
        except Exception as e:
            errs.append("Windows voice: %s" % e)
        finally:
            try:
                os.remove(raw)
            except Exception:
                pass
    if not engine:
        raise RuntimeError("; ".join(errs))
    sec = wav_seconds(out)
    _tts_dur_cache[text] = sec
    return out, sec, engine


def scene_seconds_for(speech_secs):
    """Keep the normal scene length unless the spoken line needs more; never cut speech."""
    if speech_secs <= 0:
        return SCENE_SECS
    return max(SCENE_SECS, TTS_LEAD + speech_secs + TTS_TAIL + XFADE_SECS)


def build_narration(segments, total, out_wav):
    """segments: [(start_sec, wav_path)] -> one mono PCM track of exactly `total` seconds."""
    import wave
    n = int(round(total * TTS_RATE))
    buf = bytearray(n * 2)
    for start, path in segments:
        with wave.open(path, "rb") as w:
            data = w.readframes(w.getnframes())
        off = int(round(start * TTS_RATE)) * 2
        end = min(len(buf), off + len(data))
        if end > off:
            buf[off:end] = data[:end - off]
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TTS_RATE)
        w.writeframes(bytes(buf))
    return out_wav


def _wrap_caption(d, text, font, maxw):
    lines, cur = [], ""
    tokens = re.findall(r"\S+\s*", text) if " " in text else list(text)
    for tok in tokens:
        trial = cur + tok
        if d.textlength(trial.rstrip(), font=font) <= maxw or not cur:
            if d.textlength(trial.rstrip(), font=font) > maxw and not cur and len(tok) > 1:
                # very long token (no spaces, e.g. Japanese): break per character
                for ch in tok:
                    if d.textlength((cur + ch).rstrip(), font=font) > maxw and cur:
                        lines.append(cur.rstrip())
                        cur = ch
                    else:
                        cur += ch
                continue
            cur = trial
        else:
            lines.append(cur.rstrip())
            cur = tok.lstrip()
    if cur.strip():
        lines.append(cur.rstrip())
    return lines


def draw_caption(frame, text):
    """Burn a clean caption into the lower part of a 16:9 frame (KO/JA/EN via Noto Sans KR)."""
    text = clean_caption(text)
    if not text:
        return frame
    fr = frame.convert("RGB").copy()
    W, H = fr.size
    size = max(14, int(H * 0.050))
    # Bold KR face covers Hangul/Latin/kana; full CJK face for kanji/hanja so nothing renders as boxes.
    cjk = bool(_HAN.search(text))
    font = pil_font(size, bold=not cjk, mixed=cjk)
    d = ImageDraw.Draw(fr)
    lines = _wrap_caption(d, text, font, W * 0.80)
    if len(lines) > 3:
        lines = lines[:3]
        lines[-1] = lines[-1][:max(1, len(lines[-1]) - 1)] + "…"
    lh = int(size * 1.38)
    block_h = lh * len(lines)
    y0 = int(H * 0.915) - block_h
    # soft dark band for legibility on bright pictures
    band = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(band)
    g_top = y0 - int(size * 2.2)
    g_len = max(1, int(size * 2.0))
    for i in range(g_len):
        bd.line([(0, g_top + i), (W, g_top + i)], fill=int(120 * (i + 1) / g_len))
    bd.rectangle([0, g_top + g_len, W, H], fill=120)
    fr = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), fr, band)
    d = ImageDraw.Draw(fr)
    stroke = max(1, size // 14) + (1 if cjk else 0)
    for i, ln in enumerate(lines):
        d.text((W / 2, y0 + i * lh + lh / 2), ln, font=font, fill=(250, 250, 250), anchor="mm",
               stroke_width=stroke, stroke_fill=(0, 0, 0))
    return fr


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
    """Builds the timeline of RGB frames for preview/export.
    captions: optional per-scene text (burned in); durations: optional per-scene seconds."""

    def __init__(self, scenes, title, captions=None, durations=None):
        self.scenes = scenes  # list of PIL RGB images
        self.title = title or "에피소드"
        n = len(scenes)
        caps = list(captions or [])
        self.captions = [clean_caption(caps[i]) if i < len(caps) else "" for i in range(n)]
        durs = list(durations or [])
        self.durations = [max(SCENE_SECS, float(durs[i])) if i < len(durs) and durs[i] else SCENE_SECS
                          for i in range(n)]
        self.starts = []
        t = TITLE_SECS
        for d in self.durations:
            self.starts.append(t)
            t += d

    def scene_start(self, i):
        return self.starts[i]

    def total_seconds(self):
        return TITLE_SECS + sum(self.durations) + END_SECS

    def _scene_frame(self, idx, local, span):
        progress = max(0.0, min(1.0, local / span))
        pan0, pan1 = scene_pan_for_index(idx)
        pan = (lerp(pan0[0], pan1[0], progress), lerp(pan0[1], pan1[1], progress))
        zoom = lerp(1.0, ZOOM_END, progress)
        fr = fit_cover(self.scenes[idx], OUT_W, OUT_H, zoom=zoom, pan=pan)
        if self.captions[idx]:
            fr = draw_caption(fr, self.captions[idx])
        return fr

    def frame_at(self, t):
        """Return a finished 16:9 RGB frame at time t (seconds)."""
        if t < TITLE_SECS:
            return make_title_card(self.title)
        n = len(self.scenes)
        if n == 0:
            return make_end_card(self.title)
        scenes_end = TITLE_SECS + sum(self.durations)
        if t < scenes_end:
            idx = n - 1
            for i in range(n):
                if t < self.starts[i] + self.durations[i]:
                    idx = i
                    break
            span = self.durations[idx]
            local = t - self.starts[idx]
            fr = self._scene_frame(idx, local, span)
            # crossfade into next near end of scene
            if local >= span - XFADE_SECS:
                fade = (local - (span - XFADE_SECS)) / XFADE_SECS
                if idx + 1 < n:
                    pan0b, _ = scene_pan_for_index(idx + 1)
                    fr2 = fit_cover(self.scenes[idx + 1], OUT_W, OUT_H, zoom=1.0, pan=pan0b)
                    if self.captions[idx + 1]:
                        fr2 = draw_caption(fr2, self.captions[idx + 1])
                    fr = blend(fr, fr2, fade)
                else:
                    fr = blend(fr, make_end_card(self.title), fade)
            return fr
        return make_end_card(self.title)


def prepare_narration(captions, status=None):
    """Make TTS for each non-empty caption. Returns (wavs, durations, warnings).
    Empty captions -> no audio, normal scene length."""
    wavs, durs, warns = [], [], []
    for i, cap in enumerate(captions):
        cap = clean_caption(cap)
        if not cap:
            wavs.append(None)
            durs.append(SCENE_SECS)
            continue
        if status:
            status(i, len(captions))
        try:
            wav, sec, _eng = tts_wav(cap)
        except Exception as e:
            wavs.append(None)
            durs.append(SCENE_SECS)
            warns.append("장면 %d: 음성을 만들지 못했습니다 (%s)" % (i + 1, str(e)[:160]))
            continue
        wavs.append(wav)
        durs.append(scene_seconds_for(sec))
    return wavs, durs, warns


def export_episode(scenes, title, out_path, progress=None, captions=None, tts_status=None):
    """Render the episode. Optional per-scene captions are burned in and narrated.
    Returns list of warnings (empty when everything worked)."""
    captions = [clean_caption(c) for c in (captions or [])] + [""] * max(0, len(scenes) - len(captions or []))
    wavs, durs, warns = prepare_narration(captions, tts_status) if any(captions) else ([None] * len(scenes), [SCENE_SECS] * len(scenes), [])
    comp = EpisodeComposer(scenes, title, captions=captions, durations=durs)
    total = comp.total_seconds()
    nframes = max(1, int(total * FPS))
    total = nframes / float(FPS)
    ff = ffmpeg_exe()
    narration = None
    segs = [(comp.scene_start(i) + TTS_LEAD, w) for i, w in enumerate(wavs) if w]
    if segs:
        narration = os.path.join(tempfile.mkdtemp(prefix="gaechu_tts_"), "narration.wav")
        build_narration(segs, total, narration)
    cmd = [
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (OUT_W, OUT_H),
        "-r", str(FPS), "-i", "-",
    ]
    if narration:
        cmd += ["-i", narration, "-map", "0:v", "-map", "1:a",
                "-c:a", "aac", "-b:a", "160k", "-ar", str(TTS_RATE), "-shortest"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "20",
            "-movflags", "+faststart", out_path]
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=NO_WINDOW)
    except Exception as e:
        raise RuntimeError("인코더를 시작하지 못했습니다: %s" % e)
    err = b""
    errbuf = []
    t_err = threading.Thread(target=lambda: errbuf.append(proc.stderr.read() if proc.stderr else b""), daemon=True)
    t_err.start()
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
        rc = proc.wait(timeout=180)
        t_err.join(5)
        err = errbuf[0] if errbuf else b""
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        raise RuntimeError(str(e))
    finally:
        if narration:
            shutil.rmtree(os.path.dirname(narration), ignore_errors=True)
    if rc != 0 or not os.path.isfile(out_path) or os.path.getsize(out_path) < 1000:
        raise RuntimeError("영상 내보내기 실패: " + (err.decode("utf-8", "replace")[-400:] if err else "unknown"))
    return warns


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
        self.tab = "maker"  # home | maker — default maker board
        self.library = load_library()
        self._home_photos = []
        self._nav = {}
        self.player_path = None
        self.player_title = ""
        self.player_proc = None
        self.player_playing = False
        self.player_t = 0.0
        self.player_dur = 0.0
        self.player_w = 960
        self.player_h = 540
        self.player_job = None
        self.player_seeking = False
        self.player_frame = None
        self._player_photo = None
        self._fullscreen = False
        self._cap_job = None
        self._cells = []
        self._audio_tmp = None
        self._style()
        self._build()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(200, self._refresh_home)
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
        self._nav = {}
        for key, label in (("home", "에피소드"), ("maker", "⌂  개추 트래스")):
            f = tk.Frame(nav, bg=PANEL)
            f.pack(side="left", padx=2, fill="y")
            l = tk.Label(f, text=label, bg=PANEL, fg=(TXT if key == "maker" else MUT), font=(FONT_UI, 10, "bold"),
                         padx=14, pady=8, cursor="hand2")
            l.pack(side="top", fill="y", expand=True)
            bar = tk.Frame(f, bg=RED if key == "maker" else PANEL, height=3)
            bar.pack(side="bottom", fill="x")
            l.bind("<Button-1>", lambda e, k=key: self.show_tab(k))
            f.bind("<Button-1>", lambda e, k=key: self.show_tab(k))
            self._nav[key] = {"frame": f, "label": l, "bar": bar}

        tk.Label(self, text=COPYRIGHT, bg=PANEL, fg=DIM, font=(FONT_UI, 8), pady=3).pack(side="bottom", fill="x")

        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)

        # ---- Episode home ----
        self.page_home = tk.Frame(self.body, bg=BG)
        self._build_home(self.page_home)

        # ---- Maker / board ----
        self.page_maker = tk.Frame(self.body, bg=BG)
        self._build_maker(self.page_maker)

        self.page_player = tk.Frame(self.body, bg="#000000")
        self._build_player(self.page_player)

        self.page_home.pack_forget()
        self.page_maker.pack_forget()
        self.page_player.pack_forget()
        self.show_tab("maker")

    def _build_home(self, root):
        head = tk.Frame(root, bg=BG)
        head.pack(fill="x", padx=22, pady=(18, 8))
        tk.Label(head, text="에피소드", bg=BG, fg=TXT, font=(FONT_UI, 20, "bold")).pack(side="left")
        tk.Label(head, text="내가 만든 에피소드", bg=BG, fg=MUT, font=(FONT_UI, 10)).pack(side="left", padx=(12, 0), pady=(8, 0))
        Btn(head, "＋  새로 만들기", lambda: self.show_tab("maker"), fill=RED, fg="white", hover=RED2).pack(side="right")

        self.home_status = tk.Label(root, text="", bg=BG, fg=MUT, font=(FONT_UI, 9), anchor="w")
        self.home_status.pack(fill="x", padx=22, pady=(0, 4))

        wrap = tk.Frame(root, bg=BG)
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.home_canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        self.home_scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.home_canvas.yview)
        self.home_canvas.configure(yscrollcommand=self.home_scroll.set)
        self.home_scroll.pack(side="right", fill="y")
        self.home_canvas.pack(side="left", fill="both", expand=True)
        self.home_inner = tk.Frame(self.home_canvas, bg=BG)
        self.home_win = self.home_canvas.create_window((0, 0), window=self.home_inner, anchor="nw")
        self.home_inner.bind("<Configure>", lambda e: self.home_canvas.configure(
            scrollregion=self.home_canvas.bbox("all")))
        self.home_canvas.bind("<Configure>", lambda e: self.home_canvas.itemconfigure(
            self.home_win, width=e.width))

    def _build_maker(self, root):
        bar = tk.Frame(root, bg=BG)
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

        stat = tk.Frame(root, bg=BG)
        stat.pack(side="bottom", fill="x", padx=16, pady=(0, 6))
        self.status = tk.Label(stat, text="다운로드에서 그림이나 사진을 올려 시작하세요.", bg=BG, fg=MUT,
                               font=(FONT_UI, 9), anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        self.prog = ttk.Progressbar(stat, style="red.Horizontal.TProgressbar", length=180,
                                    mode="determinate", maximum=1.0)

        strip_wrap = tk.Frame(root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
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

        self.strip_canvas = tk.Canvas(strip_wrap, bg=CARD, height=118, highlightthickness=0, cursor="hand2")
        self.strip_scroll = ttk.Scrollbar(strip_wrap, orient="horizontal", command=self.strip_canvas.xview)
        self.strip_canvas.configure(xscrollcommand=self.strip_scroll.set)
        self.strip_canvas.pack(fill="x", padx=8, pady=(4, 0))
        self.strip_scroll.pack(fill="x", padx=8, pady=(0, 8))
        self.strip_inner = tk.Frame(self.strip_canvas, bg=CARD)
        self.strip_win = self.strip_canvas.create_window((0, 0), window=self.strip_inner, anchor="nw")
        self.strip_inner.bind("<Configure>", lambda e: self.strip_canvas.configure(
            scrollregion=self.strip_canvas.bbox("all")))

        board = tk.Frame(root, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
        board.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.canvas = tk.Canvas(board, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._on_resize())
        self.canvas.bind("<Button-1>", lambda e: self.add_images() if not self.scenes else None)

    def _build_player(self, root):
        top = tk.Frame(root, bg=PANEL)
        top.pack(fill="x")
        Btn(top, "←  에피소드", self.close_player, fill=PANEL, fg=TXT, hover=CARD2,
            font=(FONT_UI, 10, "bold")).pack(side="left", padx=10, pady=8)
        self.player_title_lbl = tk.Label(top, text="", bg=PANEL, fg=TXT, font=(FONT_UI, 13, "bold"))
        self.player_title_lbl.pack(side="left", padx=(6, 0))
        Btn(top, "전체 화면", self.toggle_fullscreen, fill=PANEL, fg=MUT, hover=CARD2,
            font=(FONT_UI, 9, "bold")).pack(side="right", padx=12)

        stage = tk.Frame(root, bg="#000000")
        stage.pack(fill="both", expand=True)
        self.player_canvas = tk.Canvas(stage, bg="#000000", highlightthickness=0)
        self.player_canvas.pack(fill="both", expand=True)
        self.player_canvas.bind("<Configure>", lambda e: self._player_redraw())
        self.player_canvas.bind("<Button-1>", lambda e: self.player_toggle())

        ctrl = tk.Frame(root, bg=PANEL)
        ctrl.pack(fill="x")
        row = tk.Frame(ctrl, bg=PANEL)
        row.pack(fill="x", padx=14, pady=(10, 4))
        self.b_p_play = Btn(row, "▶  재생", self.player_play, fill=RED, fg="white", hover=RED2,
                            font=(FONT_UI, 10, "bold"), padx=16, pady=6)
        self.b_p_play.pack(side="left")
        self.b_p_pause = Btn(row, "⏸  일시정지", self.player_pause, fill=CARD2,
                             font=(FONT_UI, 10, "bold"), padx=14, pady=6)
        self.b_p_pause.pack(side="left", padx=(8, 0))
        self.b_p_stop = Btn(row, "■  정지", self.player_stop, fill=CARD2,
                            font=(FONT_UI, 10, "bold"), padx=14, pady=6)
        self.b_p_stop.pack(side="left", padx=(8, 0))
        self.player_time_lbl = tk.Label(row, text="0:00 / 0:00", bg=PANEL, fg=MUT, font=(FONT_UI, 10))
        self.player_time_lbl.pack(side="right")

        seek_row = tk.Frame(ctrl, bg=PANEL)
        seek_row.pack(fill="x", padx=14, pady=(0, 12))
        self.player_seek = ttk.Scale(seek_row, from_=0, to=1000, orient="horizontal",
                                     command=self._on_seek_drag)
        self.player_seek.pack(fill="x")
        self.player_seek.bind("<ButtonPress-1>", lambda e: setattr(self, "player_seeking", True))
        self.player_seek.bind("<ButtonRelease-1>", self._on_seek_release)

    def show_tab(self, key):
        if key not in ("home", "maker"):
            return
        if self.page_player.winfo_ismapped():
            self.player_pause()
            self._player_kill()
            if self._fullscreen:
                try:
                    self.toggle_fullscreen()
                except Exception:
                    pass
            self.page_player.pack_forget()
        self.tab = key
        for k, parts in self._nav.items():
            parts["bar"].configure(bg=RED if k == key else PANEL)
            parts["label"].configure(fg=TXT if k == key else MUT)
        self.page_player.pack_forget()
        if key == "home":
            self.page_maker.pack_forget()
            self.page_home.pack(fill="both", expand=True)
            self._refresh_home()
        else:
            self.page_home.pack_forget()
            self.page_maker.pack(fill="both", expand=True)
            self.after(50, lambda: self._draw_empty() if not self.scenes else self._show_still(self.sel or 0))

    def _refresh_home(self):
        for w in self.home_inner.winfo_children():
            w.destroy()
        self._home_photos = []
        self.library = load_library()
        eps = []
        for e in all_episodes():
            mp4, _poster = episode_paths(e)
            if e.get("bundled"):
                if os.path.isfile(mp4):
                    eps.append(e)
                continue
            if mp4 and os.path.isfile(mp4):
                eps.append(e)
        if not eps:
            empty = tk.Frame(self.home_inner, bg=BG)
            empty.pack(fill="both", expand=True, pady=80)
            try:
                lg = Image.open(res_path("assets", "icon256.png")).resize((96, 96), Image.LANCZOS)
                self._home_empty_logo = ImageTk.PhotoImage(lg)
                tk.Label(empty, image=self._home_empty_logo, bg=BG).pack()
            except Exception:
                pass
            tk.Label(empty, text=APP, bg=BG, fg=TXT, font=(FONT_UI, 18, "bold")).pack(pady=(16, 6))
            tk.Label(empty, text="아직 에피소드가 없습니다.\n개추 트래스에서 만들어 보세요.",
                     bg=BG, fg=MUT, font=(FONT_UI, 12), justify="center").pack()
            Btn(empty, "개추 트래스로 만들기", lambda: self.show_tab("maker"),
                fill=RED, fg="white", hover=RED2).pack(pady=(22, 0))
            self.home_status.configure(text="")
            return

        self.home_status.configure(text="%d개 에피소드 · 홈에서 바로 시청" % len(eps))
        self._home_card(self.home_inner, eps[0], hero_mode=True)
        row = tk.Frame(self.home_inner, bg=BG)
        row.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(row, text="내 에피소드", bg=BG, fg=MUT, font=(FONT_UI, 9, "bold")).pack(anchor="w")
        grid = tk.Frame(self.home_inner, bg=BG)
        grid.pack(fill="x", padx=4, pady=(0, 16))
        cols = 3
        for i, ep in enumerate(eps):
            cell = tk.Frame(grid, bg=BG)
            cell.grid(row=i // cols, column=i % cols, sticky="nsew", padx=8, pady=10)
            self._home_card(cell, ep, hero_mode=False)
        for c in range(cols):
            grid.grid_columnconfigure(c, weight=1)

    def _home_card(self, parent, ep, hero_mode=False):
        title = str(ep.get("title") or "에피소드")
        created = str(ep.get("created") or "")
        date_txt = created[:10] if created else ""
        mp4, poster_path = episode_paths(ep)
        featured = bool(ep.get("bundled"))

        if hero_mode:
            card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", padx=8, pady=(4, 12))
            left = tk.Frame(card, bg="#000000")
            left.pack(side="left")
            ph = self._poster_photo(poster_path, (420, 236))
            if ph:
                self._home_photos.append(ph)
                lbl = tk.Label(left, image=ph, bg="#000000", cursor="hand2")
                lbl.pack()
                lbl.bind("<Button-1>", lambda e, ee=ep: self.play_episode(ee))
            right = tk.Frame(card, bg=CARD)
            right.pack(side="left", fill="both", expand=True, padx=22, pady=22)
            badge = "추천 에피소드" if featured else "최근 에피소드"
            tk.Label(right, text=badge, bg=CARD, fg=RED2, font=(FONT_UI, 9, "bold")).pack(anchor="w")
            tk.Label(right, text=title, bg=CARD, fg=TXT, font=(FONT_UI, 18, "bold"),
                     wraplength=420, justify="left").pack(anchor="w", pady=(6, 4))
            sub = str(ep.get("subtitle") or "").strip()
            if sub:
                tk.Label(right, text=sub, bg=CARD, fg=MUT, font=(FONT_UI, 11)).pack(anchor="w")
            if date_txt:
                tk.Label(right, text=date_txt, bg=CARD, fg=MUT, font=(FONT_UI, 10)).pack(anchor="w", pady=(4, 0))
            btns = tk.Frame(right, bg=CARD)
            btns.pack(anchor="w", pady=(18, 0))
            Btn(btns, "▶  재생", lambda ee=ep: self.play_episode(ee), fill=RED, fg="white", hover=RED2).pack(side="left")
            if not featured:
                Btn(btns, "삭제", lambda ee=ep: self.remove_episode(ee), fill=CARD2, fg=MUT, hover="#5a1f1f").pack(side="left", padx=(8, 0))
            return

        card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)
        ph = self._poster_photo(poster_path, (280, 158))
        if ph:
            self._home_photos.append(ph)
            lbl = tk.Label(card, image=ph, bg="#000000", cursor="hand2")
            lbl.pack(fill="x")
            lbl.bind("<Button-1>", lambda e, ee=ep: self.play_episode(ee))
        else:
            tk.Frame(card, bg="#000000", height=158).pack(fill="x")
        meta = tk.Frame(card, bg=CARD)
        meta.pack(fill="x", padx=10, pady=10)
        tk.Label(meta, text=title, bg=CARD, fg=TXT, font=(FONT_UI, 11, "bold"),
                 wraplength=250, justify="left", anchor="w").pack(fill="x")
        sub = str(ep.get("subtitle") or "").strip()
        if sub:
            tk.Label(meta, text=sub, bg=CARD, fg=MUT, font=(FONT_UI, 9)).pack(anchor="w")
        if date_txt:
            tk.Label(meta, text=date_txt, bg=CARD, fg=DIM, font=(FONT_UI, 8)).pack(anchor="w", pady=(2, 6))
        row = tk.Frame(meta, bg=CARD)
        row.pack(fill="x")
        Btn(row, "▶  재생", lambda ee=ep: self.play_episode(ee), fill=CARD2, hover=BORDER,
            font=(FONT_UI, 9, "bold"), padx=10, pady=4).pack(side="left")
        if not featured:
            Btn(row, "삭제", lambda ee=ep: self.remove_episode(ee), fill=PANEL, fg=MUT, hover="#5a1f1f",
                font=(FONT_UI, 9, "bold"), padx=10, pady=4).pack(side="right")

    def _poster_photo(self, path, size):
        try:
            if path and os.path.isfile(path):
                im = Image.open(path).convert("RGB")
            else:
                im = Image.new("RGB", size, (18, 18, 22))
            im = ImageOps.fit(im, size, Image.LANCZOS)
            return ImageTk.PhotoImage(im)
        except Exception:
            return None

    def play_episode(self, ep_or_path):
        """Open the in-app cinematic player for an episode dict or mp4 path."""
        if isinstance(ep_or_path, dict):
            ep = ep_or_path
            mp4, _p = episode_paths(ep)
            title = str(ep.get("title") or "에피소드")
        else:
            mp4 = ep_or_path
            title = os.path.splitext(os.path.basename(mp4 or ""))[0] or "에피소드"
        if not mp4 or not os.path.isfile(mp4):
            messagebox.showinfo(APP, "영상 파일을 찾을 수 없습니다.", parent=self)
            self._refresh_home()
            return
        self.open_player(mp4, title)

    def remove_episode(self, ep):
        if ep.get("bundled") or ep.get("id") == BUNDLED_EPISODE["id"]:
            messagebox.showinfo(APP, "기본 에피소드는 삭제할 수 없습니다.", parent=self)
            return
        title = str(ep.get("title") or "에피소드")
        if not messagebox.askyesno(APP, "'%s' 에피소드를 목록에서 삭제할까요?\n(저장된 MP4 파일은 그대로 둡니다.)" % title, parent=self):
            return
        eid = ep.get("id")
        self.library = [e for e in load_library() if e.get("id") != eid]
        save_library(self.library)
        poster = ep.get("poster") or ""
        try:
            if poster and poster.startswith(app_data_dir()) and os.path.isfile(poster):
                os.remove(poster)
        except Exception:
            pass
        self._refresh_home()

    # -------------------- in-app player --------------------
    def open_player(self, path, title):
        self.stop()  # stop maker preview if any
        self._player_kill()
        self.player_path = path
        self.player_title = title
        self.player_title_lbl.configure(text=title)
        self.player_t = 0.0
        self.player_dur = probe_duration(path) or 41.5
        self.player_playing = False
        self.player_seek.set(0)
        self._update_player_time()
        self.page_home.pack_forget()
        self.page_maker.pack_forget()
        self.page_player.pack(fill="both", expand=True)
        # show poster/first frame then autoplay
        self._player_show_still(0.0)
        self.after(200, self.player_play)

    def close_player(self):
        self.player_pause()
        self._player_kill()
        if self._fullscreen:
            try:
                self.toggle_fullscreen()
            except Exception:
                pass
        self.page_player.pack_forget()
        key = self.tab if self.tab in ("home", "maker") else "home"
        self.show_tab(key)

    def toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        try:
            self.attributes("-fullscreen", self._fullscreen)
        except Exception:
            self.state("zoomed" if self._fullscreen else "normal")

    def player_toggle(self):
        if self.player_playing:
            self.player_pause()
        else:
            self.player_play()

    def player_play(self):
        if not self.player_path:
            return
        if self.player_t >= max(0.1, self.player_dur - 0.15):
            self.player_t = 0.0
        self.player_playing = True
        self._player_start_pipe(self.player_t)
        self._player_tick()

    def player_pause(self):
        self.player_playing = False
        if self.player_job:
            try:
                self.after_cancel(self.player_job)
            except Exception:
                pass
            self.player_job = None
        # keep current frame; kill pipe so seek can restart cleanly
        self._player_kill()

    def player_stop(self):
        self.player_pause()
        self.player_t = 0.0
        self.player_seek.set(0)
        self._update_player_time()
        self._player_show_still(0.0)

    def _player_audio_stop(self):
        if os.name == "nt":
            try:
                import winsound
                winsound.PlaySound(None, 0)
            except Exception:
                pass

    def _player_audio_start(self, start_t):
        """Play the episode's sound track (e.g. TTS SUBTITLES narration) from start_t. Silent files: nothing."""
        if os.name != "nt" or not self.player_path:
            return
        try:
            import winsound
            if not self._audio_tmp:
                self._audio_tmp = os.path.join(tempfile.gettempdir(), "gaechu_trass_player.wav")
            self._player_audio_stop()
            p = run_hidden([ffmpeg_exe(), "-y", "-loglevel", "error", "-ss", "%.3f" % max(0.0, start_t),
                            "-i", self.player_path, "-vn", "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le",
                            self._audio_tmp], timeout=30)
            if p.returncode == 0 and os.path.isfile(self._audio_tmp) and os.path.getsize(self._audio_tmp) > 1000:
                winsound.PlaySound(self._audio_tmp, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

    def _player_kill(self):
        self._player_audio_stop()
        proc = self.player_proc
        self.player_proc = None
        if proc is None:
            return
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=1)
        except Exception:
            pass

    def _player_start_pipe(self, start_t):
        self._player_kill()
        ff = ffmpeg_exe()
        # Scale for smooth UI playback; letterbox is applied when drawing
        w, h = self.player_w, self.player_h
        cmd = [
            ff, "-hide_banner", "-loglevel", "error",
            "-ss", "%.3f" % max(0.0, start_t),
            "-i", self.player_path,
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:black" % (w, h, w, h),
            "-an", "-sn", "-r", str(FPS), "-"
        ]
        self._player_audio_start(start_t)
        try:
            self.player_proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                bufsize=w * h * 3 * 2, creationflags=NO_WINDOW)
            self._pipe_t0 = time.time()
            self._pipe_start = start_t
        except Exception as e:
            self.player_proc = None
            messagebox.showerror(APP, "재생을 시작할 수 없습니다:\n%s" % e, parent=self)
            self.player_playing = False

    def _player_read_frame(self):
        proc = self.player_proc
        if not proc or not proc.stdout:
            return None
        need = self.player_w * self.player_h * 3
        buf = b""
        while len(buf) < need:
            chunk = proc.stdout.read(need - len(buf))
            if not chunk:
                return None
            buf += chunk
        return Image.frombytes("RGB", (self.player_w, self.player_h), buf)

    def _player_tick(self):
        if not self.player_playing:
            return
        im = self._player_read_frame()
        if im is None:
            self.player_playing = False
            self.player_t = self.player_dur
            self._update_player_time()
            self._player_kill()
            return
        self.player_frame = im
        elapsed = time.time() - self._pipe_t0
        self.player_t = min(self.player_dur, self._pipe_start + elapsed)
        if not self.player_seeking and self.player_dur > 0:
            self.player_seek.set(1000.0 * self.player_t / self.player_dur)
        self._update_player_time()
        self._player_redraw()
        self.player_job = self.after(int(1000 / FPS), self._player_tick)

    def _player_show_still(self, t):
        """Grab a single frame at t via ffmpeg for poster/seek preview."""
        ff = ffmpeg_exe()
        w, h = self.player_w, self.player_h
        cmd = [
            ff, "-hide_banner", "-loglevel", "error",
            "-ss", "%.3f" % max(0.0, t), "-i", self.player_path,
            "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-vf", "scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:black" % (w, h, w, h),
            "-"
        ]
        try:
            p = subprocess.run(cmd, capture_output=True, timeout=20)
            need = w * h * 3
            if p.stdout and len(p.stdout) >= need:
                self.player_frame = Image.frombytes("RGB", (w, h), p.stdout[:need])
                self._player_redraw()
        except Exception:
            pass

    def _player_redraw(self):
        cv = getattr(self, "player_canvas", None)
        if cv is None:
            return
        cw, ch = max(1, cv.winfo_width()), max(1, cv.winfo_height())
        cv.delete("all")
        im = self.player_frame
        if im is None:
            return
        # letterbox fit
        scale = min(cw / im.width, ch / im.height)
        nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
        shown = im.resize((nw, nh), Image.BILINEAR)
        self._player_photo = ImageTk.PhotoImage(shown)
        cv.create_image(cw // 2, ch // 2, image=self._player_photo)

    def _update_player_time(self):
        def fmt(s):
            s = max(0, int(s))
            return "%d:%02d" % (s // 60, s % 60)
        if hasattr(self, "player_time_lbl"):
            self.player_time_lbl.configure(text="%s / %s" % (fmt(self.player_t), fmt(self.player_dur)))

    def _on_seek_drag(self, _val=None):
        if not self.player_seeking or self.player_dur <= 0:
            return
        self.player_t = (float(self.player_seek.get()) / 1000.0) * self.player_dur
        self._update_player_time()

    def _on_seek_release(self, _e=None):
        self.player_seeking = False
        if self.player_dur <= 0 or not self.player_path:
            return
        self.player_t = (float(self.player_seek.get()) / 1000.0) * self.player_dur
        was = self.player_playing
        self.player_pause()
        self._player_show_still(self.player_t)
        if was:
            self.player_play()

    def _register_export(self, out, title, poster_im=None):
        """Add an exported episode to the home library."""
        eid = time.strftime("%Y%m%d%H%M%S") + "-%d" % (int(time.time() * 1000) % 1000)
        poster_path = ""
        try:
            if poster_im is not None:
                poster_path = os.path.join(app_data_dir(), "posters", eid + ".jpg")
                poster_im.convert("RGB").resize((640, 360), Image.LANCZOS).save(poster_path, "JPEG", quality=88)
        except Exception:
            poster_path = ""
        entry = {
            "id": eid,
            "title": title,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "mp4": out,
            "poster": poster_path,
        }
        eps = load_library()
        eps.insert(0, entry)
        save_library(eps)
        self.library = eps
        return entry

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
            self._show_still(self.sel or 0)

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
        cap = clean_caption(self.scenes[idx].get("caption", ""))
        if cap:
            im = draw_caption(im, cap)
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
            self.scenes.append(self._new_scene(p, im, tk_thumb))
            added += 1
        if added:
            self.sel = len(self.scenes) - 1
            self._refresh_strip()
            self._show_still(self.sel)
            self.set_status("%d장 추가됨 · 장면 %d장" % (added, len(self.scenes)), GREEN)

    def _refresh_strip(self):
        """Rebuild scene cells. Each scene owns its own optional TTS SUBTITLES field (kept on reorder)."""
        for w in self.strip_inner.winfo_children():
            w.destroy()
        self.strip_photos = []
        self._cells = []
        for i, sc in enumerate(self.scenes):
            on = (i == self.sel)
            cell = tk.Frame(self.strip_inner, bg=RED if on else CARD2, highlightthickness=0, padx=2, pady=2)
            cell.pack(side="left", padx=4, pady=4)
            inner = tk.Frame(cell, bg=CARD)
            inner.pack()
            left = tk.Frame(inner, bg=CARD)
            left.pack(side="left")
            lbl = tk.Label(left, image=sc["thumb"], bg=CARD, cursor="hand2")
            lbl.pack()
            cap = tk.Label(left, text="%d" % (i + 1), bg=CARD, fg=TXT, font=(FONT_UI, 8, "bold"))
            cap.pack()
            right = tk.Frame(inner, bg=CARD)
            right.pack(side="left", fill="y", padx=(6, 6), pady=(2, 2))
            tk.Label(right, text="TTS SUBTITLES", bg=CARD, fg=MUT, font=(FONT_UI, 7, "bold"),
                     anchor="w").pack(fill="x")
            ent_wrap = tk.Frame(right, bg=CARD)
            ent_wrap.pack(fill="x", pady=(2, 4))
            ent = tk.Entry(ent_wrap, textvariable=sc["cap_var"], bg=PANEL, fg=TXT, insertbackground=RED,
                           relief="flat", font=(FONT_MIX, 9), width=26,
                           highlightthickness=1, highlightbackground=BORDER, highlightcolor=RED)
            ent.pack(fill="x", ipady=3)
            ph = tk.Label(ent_wrap, text="(선택) 입력하면 화면 자막 + 음성", bg=PANEL, fg=DIM,
                          font=(FONT_UI, 8), anchor="w", cursor="xterm")
            sc["_ent"], sc["_ph"] = ent, ph
            self._sync_placeholder(sc)
            ph.bind("<Button-1>", lambda e, en=ent: en.focus_set())
            ent.bind("<FocusIn>", lambda e, idx=i, s_=sc: (s_["_ph"].place_forget(), self._select(idx)))
            ent.bind("<FocusOut>", lambda e, s_=sc: self._sync_placeholder(s_))
            ent.bind("<Return>", lambda e: self.focus_set())
            Btn(right, "▶ 미리 듣기", lambda s_=sc: self.preview_tts(s_), fill=CARD2, fg=MUT, hover=BORDER,
                font=(FONT_UI, 8, "bold"), padx=8, pady=2).pack(anchor="w")
            for w in (cell, inner, left, lbl, cap):
                w.bind("<Button-1>", lambda e, idx=i: self._select(idx))
                w.bind("<Double-Button-1>", lambda e, idx=i: self._show_still(idx))
            self.strip_photos.append(sc["thumb"])
            self._cells.append(cell)

    def _sync_placeholder(self, sc):
        ent, ph = sc.get("_ent"), sc.get("_ph")
        if not ent or not ph:
            return
        try:
            focused = (self.focus_get() is ent)
        except Exception:
            focused = False
        if sc["cap_var"].get() or focused:
            ph.place_forget()
        else:
            ph.place(x=6, rely=0.5, anchor="w")

    def _on_caption_change(self, sc):
        sc["caption"] = sc["cap_var"].get()
        if sc.get("_ph") and sc["caption"]:
            sc["_ph"].place_forget()
        if self.playing or not self.scenes:
            return
        if self._cap_job:
            try:
                self.after_cancel(self._cap_job)
            except Exception:
                pass
        def redraw():
            self._cap_job = None
            if sc in self.scenes and not self.playing:
                i = self.scenes.index(sc)
                if i == self.sel:
                    self._show_still(i)
        self._cap_job = self.after(120, redraw)

    def _new_scene(self, p, im, thumb):
        sc = {"path": p, "name": os.path.basename(p), "im": im, "thumb": thumb, "caption": ""}
        var = tk.StringVar(self, value="")
        var.trace_add("write", lambda *_a, s_=sc: self._on_caption_change(s_))
        sc["cap_var"] = var
        return sc

    def _captions(self):
        return [clean_caption(sc.get("caption", "")) for sc in self.scenes]

    def preview_tts(self, sc):
        """미리 듣기: speak this scene's TTS SUBTITLES (optional)."""
        text = clean_caption(sc["cap_var"].get())
        if not text:
            self.set_status("이 장면에는 TTS SUBTITLES가 없습니다 (선택 사항).", MUT)
            return
        if sc in self.scenes:
            self._select(self.scenes.index(sc))
        self.set_status("음성 만드는 중…", TXT)

        def work():
            try:
                wav, sec, eng = tts_wav(text)
            except Exception as e:
                self.after(0, lambda: self.set_status("미리 듣기 실패: %s" % str(e)[:200], RED2))
                return
            self.after(0, lambda: self._play_wav(wav, sec, eng))
        threading.Thread(target=work, daemon=True).start()

    def _play_wav(self, wav, sec, eng):
        voice = eng.split(":", 1)[-1] if eng and eng != "cache" else ""
        self.set_status("미리 듣기 · %.1f초%s" % (sec, (" · " + voice) if voice else ""), GREEN)
        if os.name == "nt":
            try:
                import winsound
                winsound.PlaySound(wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception:
                pass
        open_media(wav)

    def _select(self, idx):
        prev = self.sel
        self.sel = idx
        cells = getattr(self, "_cells", [])
        if len(cells) != len(self.scenes):
            self._refresh_strip()
        else:
            for i, c in enumerate(cells):
                c.configure(bg=RED if i == idx else CARD2)
        if not self.playing and (prev != idx or True):
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
        caps = self._captions()
        durs = [scene_seconds_for(_tts_dur_cache.get(c, 0.0)) if c else SCENE_SECS for c in caps]
        self._composer = EpisodeComposer(imgs, self.ep_title.get(), captions=caps, durations=durs)
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
        caps = self._captions()
        self._busy(True)
        self.prog.pack(side="right", padx=(8, 0))
        self.prog["value"] = 0
        self.set_status("내보내는 중…", TXT)

        def prog(v):
            self.after(0, lambda: (self.prog.configure(value=v),
                                   self.set_status("내보내는 중… %d%%" % int(v * 100), TXT)))

        def tts_stat(i, n):
            self.after(0, lambda: self.set_status("TTS SUBTITLES 음성 만드는 중… 장면 %d/%d" % (i + 1, n), TXT))

        def work():
            try:
                warns = export_episode(imgs, title, out, progress=prog, captions=caps, tts_status=tts_stat)
            except Exception as e:
                self.after(0, lambda: self._export_done(None, str(e)))
            else:
                self.after(0, lambda: self._export_done(out, None, warns))

        threading.Thread(target=work, daemon=True).start()

    def _export_done(self, out, err, warns=None):
        self._busy(False)
        self.prog.pack_forget()
        if err:
            self.set_status("내보내기 실패: " + err, RED2)
            messagebox.showerror(APP, "내보내기 실패:\n" + err, parent=self)
            return
        title = (self.ep_title.get() or "에피소드").strip() or "에피소드"
        poster_im = None
        try:
            if self.scenes:
                poster_im = fit_cover(self.scenes[0]["im"], 640, 360, zoom=1.0, pan=(0.5, 0.5))
        except Exception:
            poster_im = None
        try:
            self._register_export(out, title, poster_im)
        except Exception as e:
            self.set_status("저장됨 (목록 등록 실패: %s): %s" % (e, out), AMBER)
        else:
            self.set_status("저장됨 · 에피소드 홈에 추가됨: " + out, GREEN)
        if warns:
            self.set_status("저장됨 (일부 음성 없음) · " + out, AMBER)
            messagebox.showwarning(APP, "영상은 저장되었습니다. 자막은 들어갔지만 일부 음성을 만들지 못했습니다:\n\n"
                                   + "\n".join(warns[:6]), parent=self)
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
        self.player_pause()
        self._player_kill()
        try:
            if self._fullscreen:
                self.attributes("-fullscreen", False)
        except Exception:
            pass
        self.destroy()


def _selftest_tts(out_dir):
    """Diagnostic: `개추 트래스.exe --selftest-tts DIR` writes ko/ja/en narration + report."""
    os.makedirs(out_dir, exist_ok=True)
    lines = []
    try:
        import edge_tts, aiohttp, certifi  # noqa: F401
        lines.append("imports ok: edge_tts aiohttp certifi")
    except Exception as e:
        lines.append("import error: %r" % e)
    for lang, text in (("ko", "안녕하세요, 개추 트래스입니다."), ("ja", "こんにちは、テストです。"), ("en", "Hello from the episode maker.")):
        try:
            wav, sec, eng = tts_wav(text)
            dst = os.path.join(out_dir, "tts_%s.wav" % lang)
            shutil.copyfile(wav, dst)
            lines.append("%s ok %.2fs %s (%s)" % (lang, sec, eng, detect_lang(text)))
        except Exception as e:
            lines.append("%s FAIL %s" % (lang, e))
    try:
        im = Image.new("RGB", (OUT_W, OUT_H), (60, 90, 120))
        draw_caption(im, "자막 テスト caption").save(os.path.join(out_dir, "caption_frame.png"))
        lines.append("caption frame ok")
    except Exception as e:
        lines.append("caption frame FAIL %s" % e)
    try:
        a = Image.new("RGB", (OUT_W, OUT_H), (40, 70, 110))
        b = Image.new("RGB", (OUT_W, OUT_H), (110, 60, 40))
        w = export_episode([a, b], "selftest", os.path.join(out_dir, "mixed.mp4"),
                           captions=["장면 하나, 음성 테스트입니다.", ""])
        lines.append("export ok warns=%r size=%d" % (w, os.path.getsize(os.path.join(out_dir, "mixed.mp4"))))
    except Exception as e:
        lines.append("export FAIL %s" % e)
    with open(os.path.join(out_dir, "selftest.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--selftest-tts":
        _selftest_tts(sys.argv[2])
        return
    app = Studio()
    app.mainloop()


if __name__ == "__main__":
    main()
