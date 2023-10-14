import faulthandler
import sys

import wx

sys.path.append("../src/")
from main_frame import MainFrame

faulthandler.enable()


class Aging(MainFrame):
    def __init__(self):
        super().__init__()
        print("aging start")
        self.aging_cnt = 0
        self.aging()

    def aging(self):
        import glob
        paths = list(glob.glob("../sample_scans/*Ampico*"))
        import random
        path = random.choice(paths)
        print(self.aging_cnt, path)
        self.aging_cnt += 1

        self.load_file(path)

        self.callback.player.emulate_on()
        self.spool.start_play = True
        # open image every 5 min
        wx.CallLater(1000 * 60 * 5, self.aging)


if __name__ == "__main__":
    import platform

    # Set windows timer precision to 1ms
    pf = platform.system()
    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeBeginPeriod(1)
        windll.shcore.SetProcessDpiAwareness(True)

    app = wx.App()
    Aging()
    app.MainLoop()
    print("main loop end")

    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeEndPeriod(1)
