# -*- coding: utf-8 -*-
"""Capture maker-default UI for 개추 트래스 1.0.2 (not shipped)."""
import os, sys, time
sys.path.insert(0, r"Z:\workspace\gaechu-trass")
os.chdir(r"Z:\workspace\gaechu-trass")
import gaechu_trass as gt
from PIL import ImageGrab

app = gt.Studio()
app.geometry("1180x860+40+40")

def grab(name):
    app.update_idletasks(); app.update()
    time.sleep(0.5); app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    im = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    im.save(r"Z:\workspace\gaechu-trass\shots\\" + name)
    return im

def go():
    # default is maker
    app.update()
    full = grab("ui_maker_1.0.2.png")
    full.crop((0, 0, full.width, min(140, full.height))).save(
        r"Z:\workspace\gaechu-trass\shots\ui_topbar_1.0.2.png")
    open(r"Z:\workspace\gaechu-trass\shots\shot_ok.txt", "w", encoding="utf-8").write(
        "ok %s default=maker tabs=에피소드,⌂ 개추 트래스\n" % gt.APP_VERSION)
    app.destroy()

app.after(2200, go)
app.mainloop()
