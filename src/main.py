import wx
import os
from vacuummeter import VacuumMeter
from midi_controller import MidiWrap
from config import ConfigMng
from input_src import InputScanImg, InputWebcam
from player_mng import PlayerMng
from controls import SpeedSlider, TrackerCtrl, WelcomeMsg
from version import APP_TILTE
import re

# import ctypes
# try:
#     ctypes.windll.shcore.SetProcessDpiAwareness(True)
# except:
#     pass


class CallBack():
    def __init__(self, player, offset, bass_vac_lv, treble_vac_lv):
        self.player = player
        self.bass_vac_meter = bass_vac_lv
        self.treble_vac_meter = treble_vac_lv
        self.offset = offset

    def call_back(self, frame, curtime):
        if self.player is not None:
            self.player.emulate(frame, curtime)
            self.bass_vac_meter.vacuum = self.player.bass_vacuum
            self.treble_vac_meter.vacuum = self.player.treble_vacuum
            self.offset.label = self.player.tracker_offset


class MainFrame(wx.Frame):

    def __init__(self):
        super().__init__(parent=None, title=APP_TILTE, style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.CLIP_CHILDREN)
        self.SetIcon(wx.Icon(os.path.join("config", "PlaySK_icon.ico"), wx.BITMAP_TYPE_ICO))
        self.SetBackgroundColour("#AAAAAA")

        scale = wx.Display().GetScaleFactor()

        self.spool = WelcomeMsg(self, size=(800, 600))

        self.midi_btn = wx.Button(self, wx.ID_ANY, size=(90, 50), label='Midi On')
        self.midi_btn.Bind(wx.EVT_BUTTON, self.midi_onoff)
        self.midi_btn.Disable()

        self.file_btn = wx.Button(self, wx.ID_ANY, size=(90, 50), label='File')
        self.file_btn.Bind(wx.EVT_BUTTON, self.open_file)

        self.speed = SpeedSlider(self, callback=self.speed_change)
        self.tracking = TrackerCtrl(self, callback=self.tracking_change)

        self.bass_vacuum_lv = VacuumMeter(self, caption="Bass Vacuum (W.G.)")
        self.treble_vacuum_lv = VacuumMeter(self, caption="Treble Vacuum (W.G.)")

        self.obj = CallBack(None, self.tracking, self.bass_vacuum_lv, self.treble_vacuum_lv)
        self.midiobj = MidiWrap()
        self.conf = ConfigMng()
        self.player_mng = PlayerMng()

        # sizer of controls
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1.Add(self.midi_btn, flag=wx.EXPAND | wx.ALL, border=5)
        self.sizer1.Add(self.file_btn, flag=wx.EXPAND | wx.ALL, border=5)

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
        self.create_status_bar(scale)
        self.Fit()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Show()

    def create_status_bar(self, scale):
        sbar = self.CreateStatusBar(4)  # midi-port, tracker-bar
        w, h = sbar.Size[:2]
        sbar.SetStatusWidths([w // 3, w // 3, w // 6, -1])
        sbar.SetBackgroundColour(wx.Colour(225, 225, 225, 255))

        # midi port
        sbar.SetStatusText("midi output :", 0)
        ports = self.midiobj.port_list
        self.port_sel = wx.Choice(sbar, wx.ID_ANY, choices=ports)
        self.port_sel.Bind(wx.EVT_CHOICE, self.change_midi_port)
        self.port_sel.SetPosition((int(80 * scale), 0))
        last_sel = ports.index(self.conf.last_midi_port) if self.conf.last_midi_port in ports else 0
        self.port_sel.SetSelection(last_sel)
        self.change_midi_port()  # call manually for init

        # tracker bar
        sbar.SetStatusText("tracker bar :", 1)
        players = self.player_mng.player_list
        self.player_sel = wx.Choice(sbar, wx.ID_ANY, choices=players)
        self.player_sel.Bind(wx.EVT_CHOICE, self.change_player)
        self.player_sel.SetPosition((int(430 * scale), 0))
        last_sel = players.index(self.conf.last_tracker) if self.conf.last_tracker in players else 0
        self.player_sel.SetSelection(last_sel)
        self.change_player()  # call manually for init

    def on_close(self, event):
        print("on_close called")
        self.conf.save_config()
        self.spool.release_src()

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
            player_tmp.tracker_offset = self.tracking.offset
            player_tmp.auto_tracking = self.tracking.is_auto_tracking

            # set spool diameter
            self.obj.player = player_tmp

    def midi_onoff(self, event):
        obj = event.GetEventObject()
        if obj.GetLabel() == "Midi On":
            self.obj.player.emulate_on()
            obj.SetLabel("Midi Off")
        else:
            self.obj.player.emulate_off()
            obj.SetLabel("Midi On")

    def open_file(self, event):
        filters = "image files (*.jpg;*.png;*.bmp) | *.jpg;*.png;*.bmp"
        with wx.FileDialog(self, "Select File", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard=filters) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return

            path = dlg.GetPath()

            self.obj.player.emulate_off()
            self.spool.release_src()
            tmp = self.spool
            self.spool = InputScanImg(self, path, fn=self.obj.call_back)
            self.Title = os.path.basename(path)
            self.sizer3.Replace(tmp, self.spool)
            tmp.Destroy()

            self.midi_btn.SetLabel("Midi On")
            self.midi_btn.Enable()

            # reset speed (tempo)
            tempo = self.get_tempo(self.Title)
            self.speed.set("Tempo", (50, 140), tempo)

    def get_tempo(self, fname):
        val = re.findall(r"tempo:?\s*(\d{2,3})", fname)
        return 80 if val is None else int(val[0])

    def speed_change(self, val):
        if hasattr(self.spool, "set_tempo"):
            self.spool.set_tempo(val)

    def tracking_change(self, autotrack, pos):
        self.obj.player.auto_tracking = autotrack
        self.obj.player.tracker_offset = pos


if __name__ == "__main__":
    import platform
    pf = platform.system()
    if pf == 'Windows':
        from ctypes import windll
        windll.winmm.timeBeginPeriod(1)

    app = wx.App()
    MainFrame()
    app.MainLoop()
    print("main loop end")

    if pf == 'Windows':
        from ctypes import windll
        windll.winmm.timeEndPeriod(1)
