import os
import platform
import sys

import wx

from config import ConfigMng
from controls import SpeedSlider, TrackerCtrl, WelcomeMsg
from input_src import InputScanImg, load_scan
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
        wx.CallAfter(self.parent.load_file, path=filenames[0])
        return True


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title=APP_TITLE, style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.CLIP_CHILDREN)
        self.SetIcon(wx.Icon(os.path.join("config", "PlaySK_icon.ico"), wx.BITMAP_TYPE_ICO))
        if platform.system() == "Windows":
            # wxpython on Windows does not support Darkmode
            self.SetBackgroundColour("#AAAAAA")

        self.img_path = None
        self.spool = WelcomeMsg(self, size=(800, 600))
        self.spool.start_worker()

        self.midi_btn = wx.Button(self, size=self.FromDIP(wx.Size((90, 50))), label="MIDI On")
        self.midi_btn.Bind(wx.EVT_BUTTON, self.midi_onoff)
        self.midi_btn.Disable()

        self.file_btn = wx.Button(self, size=self.FromDIP(wx.Size((90, 50))), label="File")
        self.file_btn.Bind(wx.EVT_BUTTON, self.open_file)

        self.speed = SpeedSlider(self, callback=self.speed_change)
        self.tracking = TrackerCtrl(self)

        self.bass_vacuum_lv = VacuumGauge(self, caption="Bass Vacuum (inches of water)")
        self.treble_vacuum_lv = VacuumGauge(self, caption="Treble Vacuum (inches of water)")

        self.adjust_btn = wx.Button(self, size=self.FromDIP(wx.Size((180, 50))), label="Adjust CIS Image")
        self.adjust_btn.Bind(wx.EVT_BUTTON, self.adjust_image)

        self.callback = CallBack(None, self.tracking, self.bass_vacuum_lv, self.treble_vacuum_lv)
        self.midiobj = MidiWrap()
        self.conf = ConfigMng()
        self.player_mng = PlayerMng()

        # sizer of controls
        border_size = self.FromDIP(5)
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1.Add(self.midi_btn, flag=wx.EXPAND | wx.ALL, border=border_size, proportion=1)
        self.sizer1.Add(self.file_btn, flag=wx.EXPAND | wx.ALL, border=border_size, proportion=1)

        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2.Add(self.sizer1, flag=wx.EXPAND)
        self.sizer2.Add(self.speed, flag=wx.EXPAND | wx.ALL, border=border_size)
        self.sizer2.Add(self.tracking, flag=wx.EXPAND | wx.ALL, border=border_size)
        self.sizer2.Add(self.bass_vacuum_lv, flag=wx.EXPAND | wx.ALL, border=border_size)
        self.sizer2.Add(self.treble_vacuum_lv, flag=wx.EXPAND | wx.ALL, border=border_size)
        self.sizer2.Add(self.adjust_btn, flag=wx.EXPAND | wx.ALL, border=border_size)

        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3.Add(self.spool)
        self.sizer3.Add(self.sizer2)
        self.SetSizer(self.sizer3)

        self.Fit()
        self.create_status_bar()
        self.Fit()

        self.droptarget = FileDrop(self)
        self.SetDropTarget(self.droptarget)
        self.adjust_btn.Hide()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Show()

        # app was opened with file
        if len(sys.argv) > 1:
            wx.CallAfter(self.load_file, path=sys.argv[1])

    def create_status_bar(self):
        self.sbar = self.CreateStatusBar(5)  # midi-port, tracker-bar
        _, h = self.sbar.Size[:2]
        self.sbar.SetStatusWidths([-5, -1, -5, -5, -5])

        # midi port
        ports = self.midiobj.port_list
        rect = self.sbar.GetFieldRect(0)
        self.port_sel = wx.Choice(self.sbar, choices=ports, size=(rect.width, h))
        self.port_sel.Bind(wx.EVT_CHOICE, self.change_midi_port)
        self.port_sel.SetPosition((rect.x, 0))
        last_sel = ports.index(self.conf.last_midi_port) if self.conf.last_midi_port in ports else 0
        self.port_sel.SetSelection(last_sel)
        self.change_midi_port()  # call manually for init

        # tracker bar
        players = self.player_mng.player_list
        rect = self.sbar.GetFieldRect(2)
        self.player_sel = wx.Choice(self.sbar, choices=players, size=(rect.width, h))
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
        self.midiobj.close_port()
        self.spool.on_destroy()
        self.bass_vacuum_lv.destroy()
        self.treble_vacuum_lv.destroy()
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
            self.callback.player = player_tmp

    def midi_onoff(self, event):
        obj = event.GetEventObject()
        if obj.GetLabel() == "MIDI On":
            self.callback.player.emulate_on()
            obj.SetLabel("MIDI Off")
        else:
            self.callback.player.emulate_off()
            obj.SetLabel("MIDI On")

    def load_file(self, path, force_manual_adjust=False):
        ext = os.path.splitext(path)[-1]
        if ext.lower() not in (".cis", ".jpg", ".png", ".tif", ".bmp"):
            wx.MessageBox("Supported image formats are .cis .jpg, .png, .tif, .bmp", "Unsupported file")
            return

        img, tempo = load_scan(path, self.callback.player.default_tempo, force_manual_adjust)
        if img is None:
            return
        self.img_path = path
        if self.img_path.lower().endswith(".cis"):
            self.adjust_btn.Show()
        else:
            self.adjust_btn.Hide()
        self.callback.player.emulate_off()
        self.spool.on_destroy()
        tmp = self.spool
        self.spool = InputScanImg(self, img, self.callback.player.spool_diameter, self.callback.player.roll_width, callback=self.callback)
        self.spool.start_worker()
        self.Title = APP_TITLE + " - " + os.path.basename(path)
        self.sizer3.Replace(tmp, self.spool)
        tmp.Destroy()

        self.midi_btn.SetLabel("MIDI On")
        self.midi_btn.Enable()

        # Set tempo
        self.speed.set("Tempo", (50, 140), tempo)

    def open_file(self, event):
        filters = "image files (*cis;*.jpg;*.png;*.tif;*.bmp)|*cis;*.jpg;*.png;*.tif;*.bmp"
        with wx.FileDialog(self, "Select File", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard=filters) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.load_file(path)

    def speed_change(self, val):
        if hasattr(self.spool, "set_tempo"):
            self.spool.set_tempo(val)

    def adjust_image(self, event):
        if self.img_path is not None:
            # re-open with manually adjust dialog
            self.load_file(self.img_path, True)


if __name__ == "__main__":
    pf = platform.system()
    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeBeginPeriod(1)
        windll.shcore.SetProcessDpiAwareness(True)
        # drop file to .exe changes current dir and causes errors, so fix current dir
        os.chdir(os.path.dirname(sys.argv[0]))

    from main import AppMain
    app = AppMain()
    if not MidiWrap().port_list:
        wx.MessageBox("No any midi out port found. Exit software.", "Midi port error")
        exit(-1)

    frame = MainFrame()
    app.MainLoop()
    print("main loop end")

    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeEndPeriod(1)
