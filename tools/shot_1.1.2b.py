# -*- coding: utf-8 -*-
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
    im = Image.new("RGB", (1280, 720), (40, 70, 110))
    path = r"Z:\workspace\gaechu-trass\shots\_ro_scene.png"
    im.save(path)
    app._add_paths([path])
    app.update(); time.sleep(0.3)
    if app.scenes:
        app.scenes[0]["cap_var"].set("Bună ziua, acesta este un test în limba română.")
        try:
            app._refresh_strip()
        except Exception:
            pass
        try:
            app._show_still(0)
        except Exception:
            pass
        app.update(); time.sleep(0.4); app.update()
    full = grab("ui_maker_ro_1.1.2.png")
    full.crop((0, 0, full.width, min(160, full.height))).save(SH + "ui_topbar_1.1.2.png")
    rgb = full.convert("RGB")
    rgb.save(STORE + "shot0.jpg", quality=88, optimize=True)
    open(SH + "shot_ok_1.1.2.txt", "w", encoding="utf-8").write(
        "ok %s scenes=%d cap=%r font_cap=%s\n" % (
            gt.APP_VERSION, len(app.scenes),
            app.scenes[0]["cap_var"].get() if app.scenes else "",
            gt.FONT_CAP))
    app.destroy()

app.after(2400, go)
app.mainloop()
