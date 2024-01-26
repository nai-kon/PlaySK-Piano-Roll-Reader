import json
import re
import threading
import urllib.request

import wx
import wx.adv
from config import ConfigMng
from version import APP_TITLE, APP_VERSION, COPY_RIGHT
from wx.lib.agw.hyperlink import HyperLinkCtrl


class WelcomeMsg(wx.Panel):
    def __init__(self, parent, pos=(0, 0), size=(800, 600)):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos, parent.FromDIP(wx.Size(size)))

        self.SetForegroundColour("white")

        dummy = wx.StaticText(self, wx.ID_ANY, "")
        msg1 = wx.StaticText(self, wx.ID_ANY, "SELECT or DROP FILE here!")
        msg1.SetFont(wx.Font(30, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD))

        msg2 = wx.StaticText(self, wx.ID_ANY, "Tip: Associate this app with .cis file, you can run app by double-clicking .cis")
        msg2.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD))

        msg3 = wx.StaticText(self, wx.ID_ANY, APP_TITLE)
        msg4 = wx.StaticText(self, wx.ID_ANY, f"Version {APP_VERSION}")
        lnk = HyperLinkCtrl(self, wx.ID_ANY, "Project page on GitHub", URL="https://github.com/nai-kon/PlaySK-Piano-Roll-Reader")
        msg5 = wx.StaticText(self, wx.ID_ANY, COPY_RIGHT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(dummy, 4, wx.ALIGN_CENTER)
        sizer.Add(msg1, 2, wx.ALIGN_CENTER)
        sizer.Add(msg2, 2, wx.ALIGN_CENTER)
        sizer.Add(msg3, 0, wx.ALIGN_CENTER)
        sizer.Add(msg4, 0, wx.ALIGN_CENTER)
        sizer.Add(lnk, 0, wx.ALIGN_CENTER)
        sizer.Add(msg5, 0, wx.ALIGN_CENTER)
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
    def __init__(self, parent, pos=(0, 0), label="Tempo", tempo_range=(50, 140), val=80, callback=None):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos)
        self.callback = callback
        self.label = label
        self.caption = wx.StaticText(self, wx.ID_ANY, f"{self.label} {val}")
        self.slider = wx.Slider(self, wx.ID_ANY, val, tempo_range[0], tempo_range[1], style=wx.SL_HORIZONTAL)
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

    def set(self, label, tempo_range, val):
        self.label = label
        self.slider.SetRange(tempo_range[0], tempo_range[1])
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
        self.auto_track = True
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
            self.auto_track = True
            self.right.Disable()
            self.left.Disable()
        else:
            self.auto_track = False
            self.right.Enable()
            self.left.Enable()

    def is_auto_tracking(self):
        return self.auto_track

    def changed(self, val):
        if self.offset != val:
            self.offset = val
            wx.CallAfter(self.label.SetLabel, f"{self.offset:+}")


class NotifyDialog(wx.Dialog):
    def __init__(self, parent, version):
        super(NotifyDialog, self).__init__(parent, title="New Release", style=wx.CAPTION)

        panel = wx.Panel(self)
        message = wx.StaticText(panel, label=f"New ver{version} has been released!")
        message.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        url = "https://github.com/nai-kon/PlaySK-Piano-Roll-Reader/releases/"
        lnk = HyperLinkCtrl(panel, label=url, URL=url)
        ok_button = wx.Button(panel, label="OK")
        ok_button.Bind(wx.EVT_BUTTON, self.on_ok)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(message, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        sizer.Add(lnk, flag=wx.ALL, border=10)
        sizer.Add(ok_button, flag=wx.ALL | wx.ALIGN_CENTER, border=10)

        panel.SetSizerAndFit(sizer)
        self.Fit()
        self.Center(wx.BOTH)
        self.ShowModal()

    def on_ok(self, event):
        self.Close()
        self.Destroy()


class NotifyUpdate:
    def __init__(self, parent: wx.Panel, conf: ConfigMng) -> None:
        self.parent = parent
        self.conf = conf
        self.url = "https://api.github.com/repos/nai-kon/PlaySK-Piano-Roll-Reader/releases/latest"

    def fetch_latest_version(self) -> str | None:
        # get from release title. If title is not format in "VerX.X", not released yet
        try:
            with urllib.request.urlopen(self.url, timeout=10) as res:
                title = json.loads(res.read().decode("utf8")).get("name", None)
                matched = re.findall(r"^Ver(\d.\d.\d)$", title)
                ver = matched[0] if matched else None
        except Exception:
            ver = None
        return ver

    def need_notify(self, ver: str | None) -> bool:
        print(ver, self.conf.update_notified_version, APP_VERSION)
        return (ver is not None and 
            ver > self.conf.update_notified_version and
            ver > APP_VERSION)

    def notify(self, ver: str) -> None:
        # once notify, no notify until next release
        self.conf.update_notified_version = ver
        wx.CallAfter(NotifyDialog, self.parent, ver)

    @classmethod
    def check(cls, parent: wx.Panel, conf: ConfigMng) -> threading.Thread:
        def check_func():
            obj = cls(parent, conf)
            latest_ver = obj.fetch_latest_version()
            if obj.need_notify(latest_ver):
                obj.notify(latest_ver)

        th = threading.Thread(target=check_func)
        th.start()
        return th


if __name__ == "__main__":
    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY)

    # panel1 = WelcomeMsg(frame)
    panel1 = TrackerCtrl(frame)
    # panel1 = SpeedSlider(frame)

    frame.Fit()
    frame.Show()
    app.MainLoop()
