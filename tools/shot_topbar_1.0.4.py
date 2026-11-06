# -*- coding: utf-8 -*-
"""Capture maker-first top bar for 개추 트래스 1.0.4 (not shipped)."""
import os, sys, time
sys.path.insert(0, r"Z:\workspace\gaechu-trass")
os.chdir(r"Z:\workspace\gaechu-trass")
import gaechu_trass as gt
from PIL import ImageGrab

SH = r"Z:\workspace\gaechu-trass\shots\\"
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
    # default is maker; nav order should be maker then home
    keys = list(app._nav.keys())
    labels = [app._nav[k]["label"].cget("text") for k in keys]
    # pack order: frames were packed left-to-right in construction order
    # verify visual by reconstructing expected order from construction
    full = grab("ui_maker_1.0.4.png")
    full.crop((0, 0, full.width, min(140, full.height))).save(SH + "ui_topbar_1.0.4.png")
    # also refresh store shot0 from maker crop/full
    store = r"Z:\workspace\gaechu-trass\store_art\\"
    # JPEG for catalog shot0
    rgb = full.convert("RGB")
    rgb.save(store + "shot0.jpg", quality=88, optimize=True)
    open(SH + "shot_ok_1.0.4.txt", "w", encoding="utf-8").write(
        "ok %s default=%s mapped_maker=%s nav_keys=%s labels=%s\n" % (
            gt.APP_VERSION, app.tab, app.page_maker.winfo_ismapped(), keys, labels))
    app.destroy()

app.after(2200, go)
app.mainloop()
