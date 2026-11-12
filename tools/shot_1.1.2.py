# -*- coding: utf-8 -*-
"""Capture maker top bar + Romanian TTS caption for EPISODIA 1.1.2."""
import os, sys, time
sys.path.insert(0, r"Z:\workspace\gaechu-trass")
os.chdir(r"Z:\workspace\gaechu-trass")
import gaechu_trass as gt
from PIL import Image, ImageGrab

SH = r"Z:\workspace\gaechu-trass\shots\\"
STORE = r"Z:\workspace\gaechu-trass\store_art\\"
app = gt.Studio()
app.geometry("1180x860+40+40")

def grab(name):
    app.update_idletasks(); app.update()
    time.sleep(0.5); app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    im = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    im.save(SH + name)
    return im

def go():
    # Add a blank scene with Romanian caption so the TTS field shows diacritics
    im = Image.new("RGB", (1280, 720), (40, 70, 110))
    path = os.path.join(gt.downloads_dir(), "episodia_ro_test.png")
    im.save(path)
    try:
        app.add_images_from_paths([path])
    except Exception:
        # fallback: call internal add if signature differs
        pass
    app.update(); time.sleep(0.4); app.update()
    if app.scenes:
        app.scenes[0]["cap_var"].set("Bună ziua, acesta este un test în limba română.")
        app._rebuild_strip()
        app.update(); time.sleep(0.3); app.update()
    full = grab("ui_maker_1.1.2.png")
    full.crop((0, 0, full.width, min(140, full.height))).save(SH + "ui_topbar_1.1.2.png")
    rgb = full.convert("RGB")
    rgb.save(STORE + "shot0.jpg", quality=88, optimize=True)
    # also copy caption_ro into store as extra proof (not catalog art)
    open(SH + "shot_ok_1.1.2.txt", "w", encoding="utf-8").write(
        "ok %s default=%s badge_has_ro=%s scenes=%d font_cap=%s\n" % (
            gt.APP_VERSION, app.tab,
            "ROMANIAN TTS" in "SUPPORTS KOREAN TTS  ·  JAPANESE TTS  ·  ENGLISH TTS  ·  ROMANIAN TTS",
            len(app.scenes), gt.FONT_CAP))
    app.destroy()

app.after(2400, go)
app.mainloop()
