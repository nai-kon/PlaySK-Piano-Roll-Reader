import platform
import threading
import time

import numpy as np
import wx

from input_src import FPScounter


class VacuumGauge(wx.Panel):
    def __init__(self, parent, pos=(0, 0), caption=""):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos=pos)
        caption = wx.StaticText(self, wx.ID_ANY, caption)
        self.meter = OscilloGraph(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(caption)
        sizer.Add(self.meter)
        self.SetSizer(sizer)
        self.Fit()

    @property
    def vacuum(self):
        return self.meter.val

    @vacuum.setter
    def vacuum(self, val):
        self.meter.val = val


class OscilloGraph(wx.Panel):
    def __init__(self, parent, pos=(0, 0), max=50, size=(200, 150)):
        size = parent.FromDIP(wx.Size(size))
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=size)
        self.w = size[0]
        self.h = size[1]
        self.max = max
        self.scale = self.GetDPIScaleFactor() if platform.system() == "Windows" else 1
        self.plot_scale = self.h / self.max
        self.SetDoubleBuffered(True)

        self.val = 0
        self.xs = np.arange(self.w, step=self.scale).astype(np.intc)
        self.ys = np.full(self.xs.size, self.h - 1, dtype=np.intc)
        self.plots = np.dstack((self.xs, self.ys))

        self.graph = wx.Bitmap(self.w, self.h)
        self.grid = wx.Bitmap(self.w, self.h)
        self.init_grid()
        self.count = FPScounter("vacuum")

        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.fps = 65

        self.worker_thread_quit = False
        self.thread_lock = threading.Lock()
        self.thread_worker = threading.Thread(target=self.load_thread)
        self.thread_worker.start()

    def on_destroy(self, event):
        self.worker_thread_quit = True
        self.thread_worker.join(timeout=3)
        # wx.GetApp().Yield(onlyIfNeeded=True)

    def init_grid(self):
        dc = wx.BufferedDC(wx.ClientDC(self), self.grid)
        dc = wx.GCDC(dc)  # for anti-aliasing

        dc.SetBackground(wx.Brush("#303030"))
        dc.Clear()

        # grid line
        dc.SetPen(wx.Pen("black", int(1 * self.scale), wx.SOLID))
        dc.DrawLineList([(x, 0, x, self.h - 1) for x in range(0, self.w, int(50 * self.scale))])
        dc.DrawLineList([(0, int(y * self.plot_scale), self.w - 1, int(y * self.plot_scale)) for y in range(0, self.max, 10)])

        # scale
        dc.SetFont(wx.Font(int(12 * self.scale), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dc.SetTextForeground((255, 255, 255))
        _, txt_h = dc.GetTextExtent("0")
        dc.DrawTextList(["40", "30", "20", "10"], [(2, int(v * self.plot_scale - txt_h // 2)) for v in [10, 20, 30, 40]])

    def load_thread(self):
        while not self.worker_thread_quit:

            t1 = time.perf_counter()

            self.ys[0:-1] = self.ys[1:]
            self.ys[-1] = np.array(self.h - self.val * self.plot_scale - 1, dtype=np.intc)

            if self.thread_lock.acquire(timeout=0):
                self.plots = np.dstack((self.xs, self.ys))
                self.thread_lock.release()
                wx.CallAfter(self.Refresh, eraseBackground=False)

            elapsed_time = time.perf_counter() - t1
            sleep_time = (1 / self.fps) - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.count()

        print("end thread")

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.grid, 0, 0)
        dc = wx.GCDC(dc)  # for anti-aliasing
        dc.SetPen(wx.Pen("yellow", int(2 * self.scale), wx.SOLID))
        with self.thread_lock:
            dc.DrawLinesFromBuffer(self.plots)


if __name__ == "__main__":
    pf = platform.system()
    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeBeginPeriod(1)
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except Exception:
        pass

    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY, "vacuum meter")
    panel1 = VacuumGauge(frame, (0, 0), "Treble Vacuum")

    def slider_value_change(event):
        obj = event.GetEventObject()
        panel1.vacuum = obj.GetValue()

    slider = wx.Slider(frame, value=0, minValue=0, maxValue=40, size=frame.FromDIP(wx.Size(200, 100)), style=wx.SL_LABELS)
    slider.Bind(wx.EVT_SLIDER, slider_value_change)

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(panel1)
    sizer.Add(slider)
    frame.SetSizer(sizer)

    frame.Show()
    app.MainLoop()

    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeEndPeriod(1)
