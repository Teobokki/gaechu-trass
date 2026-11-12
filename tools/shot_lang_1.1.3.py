# -*- coding: utf-8 -*-
"""Capture the EPISODIA maker bar with the new 음성 언어 (TTS language) selector set to Romanian, v1.1.3."""
import os, sys, time
sys.path.insert(0, r"Z:\workspace\gaechu-trass")
os.chdir(r"Z:\workspace\gaechu-trass")
import gaechu_trass as gt
from PIL import ImageGrab, Image

SH = r"Z:\workspace\gaechu-trass\shots\\"
app = gt.Studio()
app.geometry("1200x840+30+30")

def grab(name):
    app.update_idletasks(); app.update(); time.sleep(0.5); app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(SH + name)

def go():
    # a couple of placeholder scenes so the maker looks populated
    for i in range(3):
        p = r"Z:\tmp\gtshot\s%d.png" % i
        app.scenes.append(app._new_scene(p, Image.new("RGB", (640, 360), (40 + i * 30, 70, 120)),
                                         gt.ImageTk.PhotoImage(Image.new("RGB", (96, 54), (40 + i * 30, 70, 120)))))
    app.scenes[0]["cap_var"].set("Buna ziua, acesta este un test in limba romana.")
    app._refresh_strip(); app._select(0)
    # force the selector to Romanian (Emil, male) so it reads clearly in the shot
    app.ep_lang.set(gt.LANG_CODE_TO_LABEL["ro"])
    app.update()
    grab("ui_maker_lang_1.1.3.png")
    # also open the dropdown menu to show all choices
    try:
        app.lang_menu["menu"].post(app.lang_menu.winfo_rootx(),
                                   app.lang_menu.winfo_rooty() + app.lang_menu.winfo_height())
        app.update(); time.sleep(0.5); app.update()
        grab("ui_maker_lang_open_1.1.3.png")
    except Exception as e:
        open(SH + "shot_lang_err.txt", "w").write(repr(e))
    app.destroy()

app.after(2000, go)
app.mainloop()
