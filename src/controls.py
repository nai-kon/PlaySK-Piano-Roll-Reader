import wx
from wx.lib.agw.hyperlink import HyperLinkCtrl
from version import APP_TITLE, APP_VERSION, COPY_RIGHT


class WelcomeMsg(wx.Panel):
    def __init__(self, parent, pos=(0, 0), size=(800, 600)):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos, size)

        self.SetForegroundColour("white")

        dummy = wx.StaticText(self, wx.ID_ANY, "")
        msg1 = wx.StaticText(self, wx.ID_ANY, "SELECT FILE and START PLAYING!")
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

    def release_src(self):
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
        self._value_changed(val)

    def _slider_changed(self, event):
        val = event.GetEventObject().GetValue()
        self._value_changed(val)


class TrackerCtrl(wx.Panel):
    def __init__(self, parent, pos=(0, 0), callback=None):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos)
        self.callback = callback
        self.offset = 0

        # auto-tracking check box
        checkbox = wx.CheckBox(self, wx.ID_ANY, "Auto Tracking")

        # tracker offset
        self._label = wx.StaticText(self, wx.ID_ANY, "+0")
        self._label.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.left = wx.Button(self, wx.ID_ANY, label="Left")
        self.right = wx.Button(self, wx.ID_ANY, label="Right")
        self.left.Bind(wx.EVT_BUTTON, self._on_left)
        self.right.Bind(wx.EVT_BUTTON, self._on_right)
        checkbox.Bind(wx.EVT_CHECKBOX, self._on_auto)

        # init
        self.is_auto_tracking = True
        checkbox.SetValue(self.is_auto_tracking)
        self.right.Disable()
        self.left.Disable()

        sizer = wx.GridBagSizer(vgap=2, hgap=2)
        sizer.Add(checkbox, (0, 0), (1, 3), flag=wx.EXPAND)
        sizer.Add(self._label, (1, 0), (1, 1), flag=wx.EXPAND)
        sizer.Add(self.left, (1, 1), (1, 1), flag=wx.EXPAND | wx.LEFT, border=5)
        sizer.Add(self.right, (1, 2), (1, 1), flag=wx.EXPAND | wx.LEFT, border=5)
        self.SetSizer(sizer)
        self.Fit()

    @property
    def label(self):
        return self._label.GetLabel()

    @label.setter
    def label(self, val):
        if self.offset != val:
            self.offset = val
            self._label.SetLabel(f"{self.offset:+}")

    def _on_left(self, event):
        self.offset -= 1
        self._value_changed()

    def _on_right(self, event):
        self.offset += 1
        self._value_changed()

    def _on_auto(self, event):
        self.is_auto_tracking = event.GetEventObject().IsChecked()
        if self.is_auto_tracking:
            self.right.Disable()
            self.left.Disable()
        else:
            self.right.Enable()
            self.left.Enable()

        self._value_changed()

    def _value_changed(self):
        self._label.SetLabel(f"{self.offset:+}")
        if self.callback is not None:
            self.callback(self.is_auto_tracking, self.offset)


if __name__ == "__main__":
    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY)

    panel1 = WelcomeMsg(frame)

    frame.Fit()
    frame.Show()
    app.MainLoop()
