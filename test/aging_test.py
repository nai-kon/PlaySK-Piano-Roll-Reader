import faulthandler
import os
import sys

import wx

sys.path.append("../src/")
from input_src import InputScanImg
from main import MainFrame

faulthandler.enable()


class Aging(MainFrame):
    def __init__(self):
        super().__init__()
        print("aging start")
        self.aging_cnt = 0
        self.aging()

    def aging(self):
        import glob
        paths = list(glob.glob("/Users/sasaki/Desktop/output/*Ampico*"))
        import random
        path = random.choice(paths)
        print(self.aging_cnt, path)
        self.aging_cnt += 1

        self.obj.player.emulate_off()
        self.spool.release_src()
        tmp = self.spool
        self.spool = InputScanImg(
            self, path, self.obj.player.spool_diameter, self.obj.player.roll_width, callback=self.obj)
        self.spool.start_worker()
        self.Title = os.path.basename(path)
        self.sizer3.Replace(tmp, self.spool)
        tmp.Destroy()
        self.obj.player.emulate_on()
        self.spool.start_play = True
        # open image every 5 miniutes
        wx.CallLater(1000 * 60 * 5, self.aging)


if __name__ == "__main__":
    import platform

    # Set windows timer precision to 1ms
    pf = platform.system()
    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeBeginPeriod(1)

    # high DPI awareness
    # try:
    #     import ctypes
    #     ctypes.windll.shcore.SetProcessDpiAwareness(True)
    # except Exception as e:
    #     print(e)

    app = wx.App()
    Aging()
    app.MainLoop()
    print("main loop end")

    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeEndPeriod(1)
