import os
import platform
import sys
from pathlib import Path

import wx
from config import ConfigMng
from controls import NotifyUpdate, SpeedSlider, TrackerCtrl, WelcomeMsg
from input_src import InputScanImg, load_scan
from midi_controller import MidiWrap
from player_mng import PlayerMng
from vacuum_gauge import VacuumGauge
from version import APP_TITLE


class CallBack:
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

    # def key_event(self, key, keydown):
    #     if self.player is not None:
    #         self.player.expression_key_event(key, keydown)


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
        self.SetIcon(wx.Icon(os.path.join("playsk_config", "PlaySK_icon.ico"), wx.BITMAP_TYPE_ICO))
        if platform.system() == "Windows":
            # wxpython on Windows does not support Darkmode
            self.SetBackgroundColour("#AAAAAA")

        self.conf = ConfigMng()
        self.img_path = None
        self.spool = WelcomeMsg(self, size=(800, 600))
        self.spool.start_worker()

        font = wx.Font(self.get_scaled_textsize(10), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        self.midi_btn = wx.Button(self, size=self.get_dipscaled_size(wx.Size((90, 50))), label="MIDI On")
        self.midi_btn.Bind(wx.EVT_BUTTON, self.midi_onoff)
        self.midi_btn.SetFont(font)
        self.midi_btn.Disable()

        self.file_btn = wx.Button(self, size=self.get_dipscaled_size(wx.Size((90, 50))), label="File")
        self.file_btn.SetFont(font)
        self.file_btn.Bind(wx.EVT_BUTTON, self.open_file)

        self.speed = SpeedSlider(self, callback=self.speed_change)
        self.tracking = TrackerCtrl(self)

        self.bass_vacuum_lv = VacuumGauge(self, caption="Bass Vacuum (inches of water)")
        self.treble_vacuum_lv = VacuumGauge(self, caption="Treble Vacuum (inches of water)")

        self.adjust_btn = wx.Button(self, size=self.get_dipscaled_size(wx.Size((180, 50))), label="Adjust CIS Image")
        self.adjust_btn.Bind(wx.EVT_BUTTON, self.adjust_image)
        self.adjust_btn.SetFont(font)

        self.callback = CallBack(None, self.tracking, self.bass_vacuum_lv, self.treble_vacuum_lv)
        self.midiobj = MidiWrap()
        self.player_mng = PlayerMng()

        # sizer of controls
        border_size = self.get_dipscaled_size(5)
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

        # notify update
        NotifyUpdate.check(self, self.conf)

        if len(sys.argv) > 1:
            # app was opened with file
            wx.CallAfter(self.load_file, path=sys.argv[1])

    def get_dipscaled_size(self, size:wx.Size | int):
        if isinstance(size, int):
            return int(self.FromDIP(size) * self.conf.window_scale_ratio)
        else:
            return self.FromDIP(size) * self.conf.window_scale_ratio

    def get_dpiscale_factor(self):
        return self.GetDPIScaleFactor() * self.conf.window_scale_ratio if platform.system() == "Windows" else self.conf.window_scale_ratio

    def get_scaled_textsize(self, size):
        return int(size * self.conf.window_scale_ratio)

    def create_status_bar(self):
        self.sbar = self.CreateStatusBar(8)  # midi-port, tracker-bar
        _, h = self.sbar.Size[:2]
        midiout_caption = "MIDI Output :"
        tracker_caption = "Tracker Bar :"
        trwsize_caption = "Window Size :"
        midiout_caption_w = wx.Window.GetTextExtent(self, midiout_caption).Width
        tracker_caption_w = wx.Window.GetTextExtent(self, tracker_caption).Width
        wsize_caption_w = wx.Window.GetTextExtent(self, trwsize_caption).Width

        self.sbar.SetStatusWidths([midiout_caption_w, -4, -1, tracker_caption_w, -4, -3, wsize_caption_w, -1])

        # midi port
        self.sbar.SetStatusText(midiout_caption, 0)
        ports = self.midiobj.port_list
        rect = self.sbar.GetFieldRect(1)
        self.port_sel = wx.Choice(self.sbar, choices=ports, size=(rect.width, h))
        self.port_sel.Bind(wx.EVT_CHOICE, self.change_midi_port)
        self.port_sel.SetPosition((rect.x, 0))
        last_sel = ports.index(self.conf.last_midi_port) if self.conf.last_midi_port in ports else 0
        self.port_sel.SetSelection(last_sel)
        self.change_midi_port()  # call manually for init

        # tracker bar
        self.sbar.SetStatusText(tracker_caption, 3)
        players = self.player_mng.player_list
        rect = self.sbar.GetFieldRect(4)
        self.player_sel = wx.Choice(self.sbar, choices=players, size=(rect.width, h))
        self.player_sel.Bind(wx.EVT_CHOICE, self.change_player)
        self.player_sel.SetPosition((rect.x, 0))
        last_sel = players.index(self.conf.last_tracker) if self.conf.last_tracker in players else 0
        self.player_sel.SetSelection(last_sel)
        self.change_player()  # call manually for init

        # window scale
        self.sbar.SetStatusText(trwsize_caption, 6)
        # calc scales which fit in display size
        client_h = wx.Display().GetClientArea().height
        cur_h = self.GetSize()[1]

        scales = [f"{v}%" for v in range(100, 300 + 1, 25) if (v / 100) * (cur_h / self.conf.window_scale_ratio) < client_h]
        rect = self.sbar.GetFieldRect(7)
        self.scale_sel = wx.Choice(self.sbar, choices=scales, size=(rect.width, h))
        self.scale_sel.Bind(wx.EVT_CHOICE, self.change_scale)
        self.scale_sel.SetPosition((rect.x, 0))
        last_sel = scales.index(self.conf.window_scale) if self.conf.window_scale in scales else 0
        self.scale_sel.SetSelection(last_sel)

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

    # def on_keydown(self, event):
    #     keycode = event.GetUnicodeKey()
    #     self.callback.key_event(keycode, True)
    #     event.Skip()

    # def on_keyup(self, event):
    #     keycode = event.GetUnicodeKey()
    #     self.callback.key_event(keycode, False)
    #     event.Skip()

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

    def change_scale(self, event=None):
        idx = self.scale_sel.GetSelection()
        select_scale = self.scale_sel.GetString(idx)
        if select_scale != self.conf.window_scale:
            self.conf.window_scale = select_scale
            wx.MessageBox("Exit the software. Please re-start after exit.", "Change Window Size needs Restart")
            self.on_close(event=None)

    def midi_onoff(self, event):
        obj = event.GetEventObject()
        if obj.GetLabel() == "MIDI On":
            self.callback.player.emulate_on()
            obj.SetLabel("MIDI Off")
        else:
            self.callback.player.emulate_off()
            obj.SetLabel("MIDI On")

    def load_file(self, path, force_manual_adjust=False):
        ext = Path(path).suffix.lower()
        if ext.lower() not in (".cis", ".jpg", ".png", ".tif", ".bmp"):
            wx.MessageBox("Supported image formats are .cis .jpg, .png, .tif, .bmp", "Unsupported file")
            return

        img, tempo = load_scan(self, path, self.callback.player.default_tempo, force_manual_adjust)
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
        self.spool = InputScanImg(self, img, self.callback.player.spool_diameter, self.callback.player.roll_width, window_scale=self.conf.window_scale, callback=self.callback)
        self.spool.start_worker()
        # self.spool.Bind(wx.EVT_KEY_DOWN, self.on_keydown)
        # self.spool.Bind(wx.EVT_KEY_UP, self.on_keyup)
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
            self.load_file(self.img_path, force_manual_adjust=True)


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
