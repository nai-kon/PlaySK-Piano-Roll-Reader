import faulthandler
import os
import sys

import wx

sys.path.append("../src/")
from input_src import InputScanImg
from main import MainFrame

faulthandler.enable()


class Aging(MainFrame):
    def __init__(self, path):
        super().__init__()
        self.aging(path)

    def aging(self, path):
        print(path)

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
        # close app every 10 seconds and re-launch
        print("call close")
        wx.CallLater(1000 * 10, self.on_close, event=None)


if __name__ == "__main__":
    import glob
    import platform
    import random

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

    paths = list(glob.glob("roll_images/*Ampico*"))

    def launch_app():
        path = random.choice(paths)
        print("start app")
        app = wx.App()
        Aging(path)
        app.MainLoop()
        print("end app")

    aging_cnt = 0
    while True:
        launch_app()
        print("aging_cnt", aging_cnt)
        aging_cnt += 1

    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeEndPeriod(1)
