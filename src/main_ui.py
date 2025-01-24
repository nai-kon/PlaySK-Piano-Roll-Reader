import os
import platform
import sys
from pathlib import Path

import wx
from config import ConfigMng
from controls import (
    BaseButton,
    BaseCheckbox,
    NotifyUpdate,
    SpeedSlider,
    TrackerCtrl,
    WelcomeMsg,
)
from midi_controller import MidiWrap
from organ_stop_indicator import OrganStopIndicator
from player_mng import PlayerMng
from roll_scroll import InputScanImg, load_scan
from tracker_bars import BasePlayer
from vacuum_gauge import VacuumGauge
from version import APP_TITLE
from wx.adv import HyperlinkCtrl


class CallBack:
    def __init__(self, player: BasePlayer | None, tracker: TrackerCtrl, bass_vac_meter: VacuumGauge, treble_vac_meter: VacuumGauge) -> None:
        self.player = player
        self.bass_vac_meter = bass_vac_meter
        self.treble_vac_meter = treble_vac_meter
        self.tracker = tracker

    def emulate(self, frame, curtime: float) -> None:
        if self.player is not None:
            self.player.auto_tracking = self.tracker.is_auto_tracking()
            self.player.tracker_offset = self.tracker.offset
            self.player.emulate(frame, curtime)
            self.bass_vac_meter.vacuum = self.player.bass_vacuum
            self.treble_vac_meter.vacuum = self.player.treble_vacuum
            self.tracker.changed(self.player.tracker_offset)

    def key_event(self, key: int, pressed: bool) -> None:
        if self.player is not None:
            self.player.expression_key_event(key, pressed)


class FileDrop(wx.FileDropTarget):
    def __init__(self, parent):
        wx.FileDropTarget.__init__(self)
        self.parent = parent

    def OnDropFiles(self, x: int, y: int, filenames: list[str]):
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

        # Initial Welcome Message
        self.spool = WelcomeMsg(self, size=(800, 600))
        self.spool.start_worker()
        self.supported_imgs = (".cis", ".jpg", ".png", ".tif", ".bmp")

        # Midi on/off button
        self.midi_btn = BaseButton(self, size=self.get_dipscaled_size(wx.Size((90, 50))), label="MIDI On")
        self.midi_btn.Bind(wx.EVT_BUTTON, self.midi_onoff)
        self.midi_btn.Disable()
        # File Open button
        self.file_btn = BaseButton(self, size=self.get_dipscaled_size(wx.Size((90, 50))), label="File")
        self.file_btn.Bind(wx.EVT_BUTTON, self.open_file)
        # Tempo slider
        self.speed = SpeedSlider(self, callback=self.speed_change)
        # Auto Tracking on/off button
        self.tracking = TrackerCtrl(self)
        # Manual Expression on/off button
        self.manual_expression = BaseCheckbox(self, wx.ID_ANY, "Manual Expression")
        # Vacuum Graph
        self.bass_vacuum_lv = VacuumGauge(self, caption="Bass Vacuum (inches of water)")
        self.treble_vacuum_lv = VacuumGauge(self, caption="Treble Vacuum (inches of water)")
        # Organ Stop Indicator for Aeolian 176-note
        self.organ_stop_indicator = OrganStopIndicator(self)
        # Link for Aeolian 165-note Midi assignment document
        self.organ_midi_map = HyperlinkCtrl(self, wx.ID_ANY, "MIDI Output Assignment Map", "https://playsk-aeolian176note-midi-assignment.pages.dev/", style=wx.adv.HL_ALIGN_LEFT)

        # CIS Adjust button
        self.adjust_btn = BaseButton(self, size=self.get_dipscaled_size(wx.Size((180, 35))), label="Adjust CIS Image")
        self.adjust_btn.Bind(wx.EVT_BUTTON, self.adjust_image)

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
        self.sizer2.Add(self.manual_expression, flag=wx.EXPAND | wx.ALL, border=border_size)
        self.sizer2.Add(self.bass_vacuum_lv, flag=wx.EXPAND | wx.ALL, border=border_size)
        self.sizer2.Add(self.treble_vacuum_lv, flag=wx.EXPAND | wx.ALL, border=border_size)
        self.sizer2.Add(self.organ_stop_indicator, flag=wx.EXPAND | wx.ALL, border=border_size)
        self.sizer2.Add(self.organ_midi_map, flag=wx.EXPAND | wx.ALL, border=border_size)
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

        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Show()

        # notify update
        # NotifyUpdate.check(self, self.conf)

        if len(sys.argv) > 1:
            # app was opened with file
            wx.CallAfter(self.load_file, path=sys.argv[1])

        self.Bind(wx.EVT_KEY_DOWN, self.on_keydown)
        self.Bind(wx.EVT_KEY_UP, self.on_keyup)
        self.manual_expression.Bind(wx.EVT_CHECKBOX, self.on_check_manual_expression)

    def get_dipscaled_size(self, size:wx.Size | int) -> int | wx.Size:
        if isinstance(size, int):
            return int(self.FromDIP(size) * self.conf.window_scale_ratio)
        else:
            return self.FromDIP(size) * self.conf.window_scale_ratio

    def get_dpiscale_factor(self) -> float:
        return self.GetDPIScaleFactor() * self.conf.window_scale_ratio if platform.system() == "Windows" else self.conf.window_scale_ratio

    def get_scaled_textsize(self, size: int) -> int:
        return int(size * self.conf.window_scale_ratio)

    def create_status_bar(self):
        self.sbar = self.CreateStatusBar(9)  # midi-port, tracker-bar
        _, h = self.sbar.Size[:2]
        midiout_caption = "MIDI Out :"
        tracker_caption = "Tracker Bar :"
        wsize_caption = "Window Size :"
        midiout_caption_w = wx.Window.GetTextExtent(self, midiout_caption).Width
        tracker_caption_w = wx.Window.GetTextExtent(self, tracker_caption).Width
        wsize_caption_w = wx.Window.GetTextExtent(self, wsize_caption).Width

        self.sbar.SetStatusWidths([midiout_caption_w, -4, -1, tracker_caption_w, -4, -1,  -2, wsize_caption_w, -1])

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
        self.sbar.SetStatusText(wsize_caption, 7)
        # calc scales which fit in display size
        client_area = wx.Display().GetClientArea()
        cur_w, cur_h = self.GetSize()

        scales = []
        for v in range(100, 300 + 1, 5):
            if (v * cur_h / (self.conf.window_scale_ratio * 100)) < client_area.height and \
                (v * cur_w / (self.conf.window_scale_ratio * 100)) < client_area.width:
                    scales.append(f"{v}%")
        rect = self.sbar.GetFieldRect(8)
        self.scale_sel = wx.Choice(self.sbar, choices=scales, size=(rect.width, h))
        self.scale_sel.Bind(wx.EVT_CHOICE, self.change_scale)
        self.scale_sel.SetPosition((rect.x, 0))
        last_sel = scales.index(self.conf.window_scale) if self.conf.window_scale in scales else 0
        self.scale_sel.SetSelection(last_sel)

    def post_status_msg(self, msg: str):
        wx.CallAfter(self.sbar.SetStatusText, text=msg, i=6)

    def on_resize(self, event):
        # selection of status bar needs manually re-position
        # midi port sel
        rect = self.sbar.GetFieldRect(1)
        self.port_sel.SetPosition((rect.x, 0))
        # tracker bar sel
        rect = self.sbar.GetFieldRect(4)
        self.player_sel.SetPosition((rect.x, 0))
        # windows scale sel
        rect = self.sbar.GetFieldRect(8)
        self.scale_sel.SetPosition((rect.x, 0))

        event.Skip()

    def on_close(self, event):
        print("on_close called")
        self.conf.save_config()
        self.spool.on_destroy()
        self.midiobj.close_port()
        self.bass_vacuum_lv.destroy()
        self.treble_vacuum_lv.destroy()
        self.Destroy()

    def on_keydown(self, event):
        """
        manual expression key pressing
        """
        keycode = event.GetUnicodeKey()
        self.spool.set_pressed_key(keycode, True)
        self.callback.key_event(keycode, True)

    def on_keyup(self, event):
        """
        manual expression key pressing
        """
        keycode = event.GetUnicodeKey()
        self.spool.set_pressed_key(keycode, False)
        self.callback.key_event(keycode, False)

    def on_check_manual_expression(self, event):
        checked = event.GetEventObject().IsChecked()
        self.spool.set_manual_expression(checked)
        self.callback.player.manual_expression = checked

    def change_midi_port(self, event=None):
        idx = self.port_sel.GetSelection()
        port = self.port_sel.GetString(idx)
        self.conf.last_midi_port = port
        self.midiobj.open_port(port)

    def change_player(self, event=None):
        idx = self.player_sel.GetSelection()
        name = self.player_sel.GetString(idx)
        self.conf.last_tracker = name
        if (player_tmp:= self.player_mng.get_player_obj(name, self.midiobj)) is not None:
            self.midiobj.all_off()
            self.midi_btn.SetLabel("MIDI On")
            player_tmp.tracker_offset = self.tracking.offset
            player_tmp.auto_tracking = self.tracking.auto_tracking
            self.callback.player = player_tmp
            self.callback.player.manual_expression = self.manual_expression.IsChecked()

        if name == "Aeolian 176-note Pipe Organ":
            self.manual_expression.SetValue(False)
            self.spool.set_manual_expression(False)
            self.callback.player.manual_expression = False
            self.callback.player.init_stop_indicator(self.organ_stop_indicator)
            self.manual_expression.Hide()
            self.bass_vacuum_lv.Hide()
            self.treble_vacuum_lv.Hide()
            self.organ_stop_indicator.Show()
            self.organ_midi_map.Show()
        else:
            self.manual_expression.Show()
            self.bass_vacuum_lv.Show()
            self.treble_vacuum_lv.Show()
            self.organ_stop_indicator.Hide()
            self.organ_midi_map.Hide()
        self.Fit()

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
            self.midi_off()

    def midi_off(self):
        self.callback.player.emulate_off()
        self.midi_btn.SetLabel("MIDI On")

    def load_file(self, path: str, force_manual_adjust: bool=False):
        if Path(path).suffix.lower() not in self.supported_imgs:
            wx.MessageBox(f"Supported image formats are {' '.join(self.supported_imgs)}", "Unsupported file")
            return

        img, tempo = load_scan(self, path, self.callback.player.default_tempo, force_manual_adjust)
        if img is None:
            return
        self.img_path = path
        self.adjust_btn.Show() if self.img_path.lower().endswith(".cis") else self.adjust_btn.Hide()
        self.Fit()

        self.callback.player.emulate_off()
        tmp = self.spool
        self.spool = InputScanImg(self, img, self.callback.player.spool_diameter, self.callback.player.roll_width, window_scale=self.conf.window_scale, callback=self.callback)
        self.spool.manual_expression = self.manual_expression.IsChecked()
        self.Title = APP_TITLE + " - " + os.path.basename(path)
        self.sizer3.Replace(tmp, self.spool)
        tmp.on_destroy()
        tmp.Destroy()
        self.spool.start_worker()

        self.midi_btn.SetLabel("MIDI On")
        self.midi_btn.Enable()

        # Set tempo
        self.speed.set("Tempo", (30, 140), tempo)

    def open_file(self, event):
        tmp = ";".join(f"*{v}" for v in self.supported_imgs)
        filters = f"image files ({tmp})|{tmp}"
        with wx.FileDialog(self, "Select File", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST, wildcard=filters) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.load_file(path)

    def speed_change(self, val: float):
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
