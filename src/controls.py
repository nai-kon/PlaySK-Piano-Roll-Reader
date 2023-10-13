import wx
from wx.lib.agw.hyperlink import HyperLinkCtrl

from version import APP_TITLE, APP_VERSION, COPY_RIGHT


class WelcomeMsg(wx.Panel):
    def __init__(self, parent, pos=(0, 0), size=(800, 600)):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos, parent.FromDIP(wx.Size(size)))

        self.SetForegroundColour("white")

        dummy = wx.StaticText(self, wx.ID_ANY, "")
        msg1 = wx.StaticText(self, wx.ID_ANY, "SELECT or DROP FILE here!")
        msg1.SetFont(wx.Font(30, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD))

        msg2 = wx.StaticText(self, wx.ID_ANY, APP_TITLE)
        msg3 = wx.StaticText(self, wx.ID_ANY, f"Version {APP_VERSION}")
        lnk = HyperLinkCtrl(self, wx.ID_ANY, "Project page on GitHub", URL="https://github.com/nai-kon/PlaySK-Piano-Roll-Reader")
        msg4 = wx.StaticText(self, wx.ID_ANY, COPY_RIGHT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(dummy, 1, wx.ALIGN_CENTER)
        sizer.Add(msg1, 1, wx.ALIGN_CENTER)
        sizer.Add(msg2, 0, wx.ALIGN_CENTER)
        sizer.Add(msg3, 0, wx.ALIGN_CENTER)
        sizer.Add(lnk, 0, wx.ALIGN_CENTER)
        sizer.Add(msg4, 0, wx.ALIGN_CENTER)
        self.SetSizer(sizer)
        self.SetBackgroundColour("#555555")
        lnk.SetBackgroundColour("#555555")
        self.Layout()

    def start_worker(self):
        # compatible with InputVideo classes
        pass

    def on_destroy(self):
        # compatible with InputVideo classes
        pass


class SpeedSlider(wx.Panel):
    def __init__(self, parent, pos=(0, 0), label="Tempo", range=(50, 140), val=80, callback=None):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos)
        self.callback = callback
        self.label = label
        self.caption = wx.StaticText(self, wx.ID_ANY, f"{self.label} {val}")
        self.slider = wx.Slider(self, wx.ID_ANY, val, range[0], range[1], style=wx.SL_HORIZONTAL)
        self.slider.SetPageSize(5)
        self.slider.Bind(wx.EVT_SLIDER, self._slider_changed)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.caption, flag=wx.EXPAND)
        sizer.Add(self.slider, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()

    def _value_changed(self, val):
        self.caption.SetLabel(f"{self.label} {val}")
        if self.callback is not None:
            self.callback(val)

    def set(self, label, range, val):
        self.label = label
        self.slider.SetRange(range[0], range[1])
        self.slider.SetValue(val)
        wx.CallAfter(self._value_changed, val)

    def _slider_changed(self, event):
        val = event.GetEventObject().GetValue()
        self._value_changed(val)


class TrackerCtrl(wx.Panel):
    def __init__(self, parent, pos=(0, 0)):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos)

        # auto-tracking check box
        self.auto_tracking = wx.CheckBox(self, wx.ID_ANY, "Auto Tracking")
        self.auto_tracking.SetValue(True)
        self.auto_tracking.Bind(wx.EVT_CHECKBOX, self._on_auto_checked)

        # tracker offset buttons
        self.offset = 0
        self.label = wx.StaticText(self, wx.ID_ANY, "+0")
        self.label.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.left = wx.Button(self, wx.ID_ANY, label="Left")
        self.left.Disable()
        self.left.Bind(wx.EVT_BUTTON, lambda event: self.changed(self.offset - 1))
        self.right = wx.Button(self, wx.ID_ANY, label="Right")
        self.right.Bind(wx.EVT_BUTTON, lambda event: self.changed(self.offset + 1))
        self.right.Disable()

        sizer = wx.GridBagSizer(vgap=2, hgap=2)
        sizer.Add(self.auto_tracking, (0, 0), (1, 3), flag=wx.EXPAND)
        sizer.Add(self.label, (1, 0), (1, 1), flag=wx.EXPAND)
        border_size = parent.FromDIP(5)
        sizer.Add(self.left, (1, 1), (1, 1), flag=wx.EXPAND | wx.LEFT, border=border_size)
        sizer.Add(self.right, (1, 2), (1, 1), flag=wx.EXPAND | wx.LEFT, border=border_size)
        self.SetSizer(sizer)
        self.Fit()

    def _on_auto_checked(self, event):
        if event.GetEventObject().IsChecked():
            self.right.Disable()
            self.left.Disable()
        else:
            self.right.Enable()
            self.left.Enable()

    def is_auto_tracking(self):
        return self.auto_tracking.IsChecked()

    def changed(self, val):
        if self.offset != val:
            self.offset = val
            wx.CallAfter(self.label.SetLabel, f"{self.offset:+}")


if __name__ == "__main__":
    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY)

    # panel1 = WelcomeMsg(frame)
    panel1 = TrackerCtrl(frame)
    # panel1 = SpeedSlider(frame)

    frame.Fit()
    frame.Show()
    app.MainLoop()
