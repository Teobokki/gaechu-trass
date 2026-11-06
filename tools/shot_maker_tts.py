# -*- coding: utf-8 -*-
"""Capture maker UI with per-scene TTS SUBTITLES for 개추 트래스 1.0.3 (not shipped)."""
import os, sys, time
sys.path.insert(0, r"Z:\workspace\gaechu-trass")
os.chdir(r"Z:\workspace\gaechu-trass")
import gaechu_trass as gt
from PIL import ImageGrab

SH = r"Z:\workspace\gaechu-trass\shots\\"
log = []
app = gt.Studio()
app.geometry("1180x860+40+40")

def grab(name):
    app.update_idletasks(); app.update()
    time.sleep(0.6); app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    im = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    im.save(SH + name)
    return im

def go():
    log.append("default tab=%s maker_mapped=%s" % (app.tab, app.page_maker.winfo_ismapped()))
    imgs = [r"Z:\tmp\gt\src%d.jpg" % i for i in range(4)]
    app._add_paths(imgs)
    caps = ["어느 날, 우리는 바다로 떠났다.", "", "こんにちは、また会いましたね。", ""]
    for sc, c in zip(app.scenes, caps):
        sc["cap_var"].set(c)
    app._select(0)
    app.update()
    grab("ui_maker_1.0.3.png")
    # reorder keeps caption with its scene
    app.move_down()
    log.append("after move_down: " + repr([s["caption"] for s in app.scenes]))
    app.move_up()
    log.append("after move_up: " + repr([s["caption"] for s in app.scenes]))
    log.append("captions=" + repr(app._captions()))
    app._select(0); app.update()
    app.after(400, step2)

def step2():
    grab("ui_maker_1.0.3.png")
    app.show_tab("home"); app.update()
    eps = gt.all_episodes()
    app.play_episode(eps[0]); 
    app.after(3000, step3)

def step3():
    log.append("player playing=%s t=%.2f dur=%.2f" % (app.player_playing, app.player_t, app.player_dur))
    grab("ui_player_1.0.3.png")
    app.close_player()
    open(SH + "shot_ok_1.0.3.txt", "w", encoding="utf-8").write("\n".join(log) + "\n")
    app.destroy()

app.after(2200, go)
app.mainloop()
