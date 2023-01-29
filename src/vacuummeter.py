
import wx


class VacuumMeter(wx.Panel):
    def __init__(self, parent, pos=(0, 0), caption=""):
        self.scale = wx.Display().GetScaleFactor()
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
        self.scale = wx.Display().GetScaleFactor()
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=(int(size[0] * self.scale), int(size[1] * self.scale)))
        self.w = size[0]
        self.h = size[1]
        self.max = max
        self.scale = self.h / self.max
        self.SetDoubleBuffered(True)

        self.val = 0
        self.buf_val = [0] * self.w

        self.graph = wx.Bitmap(self.w, self.h)
        self.grid = wx.Bitmap(self.w, self.h)
        self.init_grid()

        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_TIMER, self.on_timer)

        interval = 1000 // 65
        self.timer = wx.Timer(self)
        self.timer.Start(interval)

    def on_destroy(self, event):
        self.timer.Stop()
        print("on destroy")

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
        self.buf_val = self.buf_val[1:] + [self.val * self.scale]
        plots = [wx.Point(x, self.h - y - 1) for x, y in enumerate(self.buf_val)]
        dc.DrawLines(plots)

        self.Refresh()

    def on_paint(self, event):
        wx.BufferedPaintDC(self, self.graph)


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
