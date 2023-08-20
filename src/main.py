import os
import platform
import re

import wx

from config import ConfigMng
from controls import SpeedSlider, TrackerCtrl, WelcomeMsg
from input_src import InputScanImg
from midi_controller import MidiWrap
from player_mng import PlayerMng
from vacuum_gauge import VacuumGauge
from version import APP_TITLE


class CallBack():
    def __init__(self, player, tracker, bass_vac_lv, treble_vac_lv):
        self.player = player
        self.bass_vac_meter = bass_vac_lv
        self.treble_vac_meter = treble_vac_lv
        self.tracker = tracker

    def emulate(self, frame, curtime):
        if self.player is not None:
            self.player.auto_tracking = self.tracker.is_auto_tracking()
            self.player.tracker_offset = self.tracker.offset
            self.player.emulate(frame, curtime)
            self.bass_vac_meter.vacuum = self.player.bass_vacuum
            self.treble_vac_meter.vacuum = self.player.treble_vacuum
            self.tracker.changed(self.player.tracker_offset)


class FileDrop(wx.FileDropTarget):
    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent

    def OnDropFiles(self, x, y, filenames):
        path = filenames[0]
        ext = os.path.splitext(path)[-1]
        if ext in (".jpg", ".png", ".bmp"):
            self.parent.load_file(path)
        else:
            wx.MessageBox("supported image formats are jpg, png, bmp", "unsupported file")

        return True


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title=APP_TITLE, style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.CLIP_CHILDREN)
        self.SetIcon(wx.Icon(os.path.join("config", "PlaySK_icon.ico"), wx.BITMAP_TYPE_ICO))
        if platform.system() == "Windows":
            # wxpython on Windows not support Darkmode
            self.SetBackgroundColour("#AAAAAA")

        self.spool = WelcomeMsg(self, size=(800, 600))
        self.spool.start_worker()

        self.midi_btn = wx.Button(self, wx.ID_ANY, size=self.FromDIP(wx.Size((90, 50))), label="MIDI On")
        self.midi_btn.Bind(wx.EVT_BUTTON, self.midi_onoff)
        self.midi_btn.Disable()

        self.file_btn = wx.Button(self, wx.ID_ANY, size=self.FromDIP(wx.Size((90, 50))), label="File")
        self.file_btn.Bind(wx.EVT_BUTTON, self.open_file)

        self.speed = SpeedSlider(self, callback=self.speed_change)
        self.tracking = TrackerCtrl(self)

        self.bass_vacuum_lv = VacuumGauge(self, caption="Bass Vacuum (inches of water)")
        self.treble_vacuum_lv = VacuumGauge(self, caption="Treble Vacuum (inches of water)")

        self.obj = CallBack(None, self.tracking, self.bass_vacuum_lv, self.treble_vacuum_lv)
        self.midiobj = MidiWrap()
        self.conf = ConfigMng()
        self.player_mng = PlayerMng()

        # sizer of controls
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1.Add(self.midi_btn, flag=wx.EXPAND | wx.ALL, border=5, proportion=1)
        self.sizer1.Add(self.file_btn, flag=wx.EXPAND | wx.ALL, border=5, proportion=1)

        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2.Add(self.sizer1, flag=wx.EXPAND)
        self.sizer2.Add(self.speed, flag=wx.EXPAND | wx.ALL, border=5)
        self.sizer2.Add(self.tracking, flag=wx.EXPAND | wx.ALL, border=5)
        self.sizer2.Add(self.bass_vacuum_lv, flag=wx.EXPAND | wx.ALL, border=5)
        self.sizer2.Add(self.treble_vacuum_lv, flag=wx.EXPAND | wx.ALL, border=5)

        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3.Add(self.spool)
        self.sizer3.Add(self.sizer2)
        self.SetSizer(self.sizer3)

        self.Fit()
        self.create_status_bar()
        self.Fit()

        self.droptarget = FileDrop(self)
        self.SetDropTarget(self.droptarget)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Show()

    def create_status_bar(self):
        self.sbar = self.CreateStatusBar(5)  # midi-port, tracker-bar
        _, h = self.sbar.Size[:2]
        self.sbar.SetStatusWidths([-5, -1, -5, -5, -5])

        # midi port
        ports = self.midiobj.port_list
        rect = self.sbar.GetFieldRect(0)
        self.port_sel = wx.Choice(self.sbar, wx.ID_ANY, choices=ports, size=(rect.width, h))
        self.port_sel.Bind(wx.EVT_CHOICE, self.change_midi_port)
        self.port_sel.SetPosition((rect.x, 0))
        last_sel = ports.index(self.conf.last_midi_port) if self.conf.last_midi_port in ports else 0
        self.port_sel.SetSelection(last_sel)
        self.change_midi_port()  # call manually for init

        # tracker bar
        players = self.player_mng.player_list
        rect = self.sbar.GetFieldRect(2)
        self.player_sel = wx.Choice(self.sbar, wx.ID_ANY, choices=players, size=(rect.width, h))
        self.player_sel.Bind(wx.EVT_CHOICE, self.change_player)
        self.player_sel.SetPosition((rect.x, 0))
        last_sel = players.index(self.conf.last_tracker) if self.conf.last_tracker in players else 0
        self.player_sel.SetSelection(last_sel)
        self.change_player()  # call manually for init

    def post_status_msg(self, msg):
        wx.CallAfter(self.sbar.SetStatusText, text=msg, i=4)

    def on_close(self, event):
        print("on_close called")
        self.conf.save_config()
        self.spool.release_src()
        self.midiobj.all_off()
        self.Destroy()

    def change_midi_port(self, event=None):
        idx = self.port_sel.GetSelection()
        port = self.port_sel.GetString(idx)
        self.conf.last_midi_port = port
        self.midiobj.open_port(port)

    def change_player(self, event=None):
        idx = self.player_sel.GetSelection()
        name = self.player_sel.GetString(idx)
        self.conf.last_tracker = name
        player_tmp = self.player_mng.get_player_obj(name, self.midiobj)
        if player_tmp is not None:
            self.midi_btn.SetLabel("MIDI On")
            player_tmp.tracker_offset = self.tracking.offset
            player_tmp.auto_tracking = self.tracking.auto_tracking
            self.obj.player = player_tmp

    def midi_onoff(self, event):
        obj = event.GetEventObject()
        if obj.GetLabel() == "MIDI On":
            self.obj.player.emulate_on()
            obj.SetLabel("MIDI Off")
        else:
            self.obj.player.emulate_off()
            obj.SetLabel("MIDI On")

    def load_file(self, path):
        self.obj.player.emulate_off()
        self.spool.release_src()
        tmp = self.spool
        self.spool = InputScanImg(self, path, self.obj.player.spool_diameter, self.obj.player.roll_width, callback=self.obj)
        self.spool.start_worker()
        self.Title = os.path.basename(path)
        self.sizer3.Replace(tmp, self.spool)
        tmp.Destroy()

        self.midi_btn.SetLabel("MIDI On")
        self.midi_btn.Enable()

        # Set tempo
        val = re.search(r"tempo:?\s*(\d{2,3})", self.Title)
        tempo = int(val.group(1)) if val is not None else self.obj.player.default_tempo
        self.speed.set("Tempo", (50, 140), tempo)

    def open_file(self, event):
        filters = "image files (*.jpg;*.png;*.bmp)|*.jpg;*.png;*.bmp"
        with wx.FileDialog(self, "Select File", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard=filters) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.load_file(path)


    def speed_change(self, val):
        if hasattr(self.spool, "set_tempo"):
            self.spool.set_tempo(val)


if __name__ == "__main__":
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
    MainFrame()
    app.MainLoop()
    print("main loop end")

    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeEndPeriod(1)
