
import wx
import numpy as np
import time
import threading
from input_src import FPScounter


class VacuumMeter(wx.Panel):
    def __init__(self, parent, pos=(0, 0), caption=""):
        self.scale = self.scale = 1
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos=(int(pos[0] * self.scale), int(pos[1] * self.scale)))
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
        self.scale = self.scale = 1
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=(int(size[0] * self.scale), int(size[1] * self.scale)))
        self.w = size[0]
        self.h = size[1]
        self.max = max
        self.scale = self.h / self.max
        self.SetDoubleBuffered(True)

        self.val = 0
        self.xs = np.arange(self.w, dtype=np.intc)
        self.ys = np.full(self.w, self.h - 1, dtype=np.intc)
        self.plots = np.dstack((self.xs, self.ys))

        self.graph = wx.Bitmap(self.w, self.h)
        self.grid = wx.Bitmap(self.w, self.h)
        self.init_grid()
        self.count = FPScounter("vacuum")

        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.fps = 65

        self.worker_thread_quit = False
        self.thread_worker = threading.Thread(target=self.load_thread)
        self.thread_worker.start()

    def on_destroy(self, event):
        self.worker_thread_quit = True
        self.thread_worker.join(timeout=3)
        wx.GetApp().Yield(onlyIfNeeded=True)

    def init_grid(self):
        dc = wx.BufferedDC(wx.ClientDC(self), self.grid)
        dc = wx.GCDC(dc)  # for anti-aliasing

        dc.SetBackground(wx.Brush("#303030"))
        dc.Clear()

        # grid line
        dc.SetPen(wx.Pen("black", 1, wx.SOLID))
        dc.DrawLineList([(x, 0, x, self.h - 1) for x in range(0, self.w, 50)])
        dc.DrawLineList([(0, int(y * self.scale), self.w - 1, int(y * self.scale)) for y in range(0, self.max, 10)])

        # scale
        dc.SetTextForeground((255, 255, 255))
        _, txt_h = dc.GetTextExtent("0")
        dc.DrawTextList(["40", "30", "20", "10"], [(2, int(v * self.scale - txt_h // 2)) for v in [10, 20, 30, 40]])

    def on_timer(self, event):
        dc = wx.BufferedDC(wx.ClientDC(self), self.graph)
        dc.DrawBitmap(self.grid, 0, 0)
        dc = wx.GCDC(dc)  # for anti-aliasing

        # graph
        dc.SetPen(wx.Pen("yellow", 2, wx.SOLID))
        self.ys[0:-1] = self.ys[1:]
        self.ys[-1] = np.array(self.h - self.val * self.scale - 1, dtype=np.intc)
        plots = np.dstack((self.xs, self.ys))
        dc.DrawLinesFromBuffer(plots)
        self.count()
        self.Refresh(eraseBackground=False)

    def load_thread(self):
        while not self.worker_thread_quit:

            t1 = time.perf_counter()

            self.ys[0:-1] = self.ys[1:]
            self.ys[-1] = np.array(self.h - self.val * self.scale - 1, dtype=np.intc)
            self.plots = np.dstack((self.xs, self.ys))
            wx.CallAfter(self.Refresh, eraseBackground=False)  # refresh from thread need call after
            elapsed_time = time.perf_counter() - t1
            sleep_time = (1/self.fps) - elapsed_time
            if sleep_time < 0:
                sleep_time = 0
            time.sleep(sleep_time)
            self.count()

        print("end thread")


    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.grid, 0, 0)
        dc = wx.GCDC(dc)  # for anti-aliasing
        dc.SetPen(wx.Pen("yellow", 2, wx.SOLID))
        dc.DrawLinesFromBuffer(self.plots)


if __name__ == "__main__":
    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY, "vacuum meter")
    panel1 = VacuumMeter(frame, (0, 0), "Treble Vacuum")

    def slider_value_change(event):
        obj = event.GetEventObject()
        panel1.vacuum = obj.GetValue()
    slider = wx.Slider(frame, value=0, minValue=0, maxValue=40, pos=(0, 200), size=(200, 100), style=wx.SL_LABELS)
    slider.Bind(wx.EVT_SLIDER, slider_value_change)

    frame.Fit()
    frame.Show()
    app.MainLoop()
