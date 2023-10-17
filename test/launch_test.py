import faulthandler
import os
import sys

import wx

sys.path.append("../src/")
os.chdir("../src/")
from main_frame import MainFrame

faulthandler.enable()


class Aging(MainFrame):
    def __init__(self, path):
        super().__init__()
        self.aging(path)

    def aging(self, path):
        print(path)
        self.load_file(path)
        self.callback.player.emulate_on()
        self.spool.start_play = True
        # close app every 10 seconds and re-launch
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
        windll.shcore.SetProcessDpiAwareness(True)

    paths = list(glob.glob("../sample_scans/*Ampico*"))

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
