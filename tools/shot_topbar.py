# -*- coding: utf-8 -*-
"""Capture home + top bar for 개추 트래스 1.0.1 (not shipped)."""
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
    app._refresh_home(); app.update()
    full = grab("ui_home_1.0.1.png")
    full.crop((0, 0, full.width, min(140, full.height))).save(
        r"Z:\workspace\gaechu-trass\shots\ui_topbar_1.0.1.png")
    # switch to maker briefly
    app.show_tab("maker"); app.update(); time.sleep(0.4)
    grab("ui_maker_1.0.1.png")
    app.show_tab("home"); app.update()
    # open player for bundled ep
    eps = gt.all_episodes()
    if eps:
        app.play_episode(eps[0])
        app.update(); time.sleep(1.2); app.update()
        grab("ui_player_1.0.1.png")
        app.close_player()
    open(r"Z:\workspace\gaechu-trass\shots\shot_ok.txt", "w", encoding="utf-8").write(
        "ok %s tabs=에피소드,⌂ 개추 트래스 bundled=%s\n" % (gt.APP_VERSION, bool(eps)))
    app.destroy()

app.after(2200, go)
app.mainloop()
