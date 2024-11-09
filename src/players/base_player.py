import json
import threading
from typing import final

import numpy as np
import wx
from midi_controller import MidiWrap


class TrackerHoles:
    def __init__(self, conf):
        self.xoffset = 0
        holes = conf["tracker_holes"]
        self.is_dark_hole = holes["is_dark_hole"]
        self.th_bright = holes["on_brightness"]
        self.lowest_note = holes["lowest_note"]

        self.open_pen = None
        self.close_pen = None

        # use numpy for fast calculation
        self.group_by_size = {}
        self.group_by_name = {}
        for name, v in holes.items():
            if isinstance(v, dict) and "w" in v:
                key = (v["w"], v["h"])
                self.group_by_size.setdefault(key, {"pos": [], "pos_xs": None, "pos_ys": None, "on_apatures": [], "off_apatures": []})
                si = len(self.group_by_size[key]["pos"])

                xs = [v["x"]]
                if isinstance(v["x"], list):
                    xs = v["x"]
                elif isinstance(v["x"], dict):
                    xs = list(v["x"].values())
                tmp = [(x, v["y"], x + v["w"], v["y"] + v["h"]) for x in xs]
                self.group_by_size[key]["pos"].extend(tmp)
                tmp = [v["on_apature"]] * len(xs)
                self.group_by_size[key]["on_apatures"].extend(tmp)
                tmp = [v["off_apature"]] * len(xs)
                self.group_by_size[key]["off_apatures"].extend(tmp)

                ei = len(self.group_by_size[key]["pos"])
                self.group_by_name.setdefault(name, [key, slice(si, ei)])

        for v in self.group_by_size.values():
            v["is_open"] = v["to_open"] = v["to_close"] = np.array([False] * len(v["pos"]))
            v["on_apatures"] = np.array(v["on_apatures"])
            v["off_apatures"] = np.array(v["off_apatures"])

        # for ROI extraction
        for k, v in self.group_by_size.items():
            v["pos_xs"] = np.array([p[0] for p in v["pos"]])[:, None, None] + np.arange(k[0])[None, :, None]
            v["pos_ys"] = np.array([p[1] for p in v["pos"]])[:, None, None] + np.arange(k[1])[None, None, :]

        # for draw holes
        self.draw_rects = []
        for k, v in self.group_by_size.items():
            for pos in v["pos"]:
                self.draw_rects.append((pos[0], pos[1], k[0] + 1, k[1] + 1))

    def set_frame(self, frame, xoffset):
        self.xoffset = xoffset

        # calc hole open ratio
        for v in self.group_by_size.values():
            # hole_list = np.array([frame[p[1]: p[3], p[0] + xoffset: p[2] + xoffset] for p in v["pos"]])
            hole_list = frame[v["pos_ys"], v["pos_xs"] + self.xoffset]  # more elegant way

            if self.is_dark_hole:
                open_ratios = (hole_list <= self.th_bright).all(axis=3).mean(axis=(2, 1))
                # open_ratios = (hole_list < self.th_bright).mean(axis=(3, 2, 1))
            else:
                open_ratios = (hole_list > self.th_bright).all(axis=3).mean(axis=(2, 1))
                # open_ratios = (hole_list > self.th_bright).mean(axis=(3, 2, 1))

            v["to_open"] = (~v["is_open"]) & (open_ratios > v["on_apatures"])  # hole is opened just now
            v["to_close"] = v["is_open"] & (open_ratios < v["off_apatures"])  # hole is closed just now
            v["is_open"] ^= (v["to_open"] | v["to_close"])  # hole is open or close

    def all_off(self):
        for v in self.group_by_size.values():
            v["is_open"] &= False
            v["to_open"] &= False
            v["to_close"] &= False

    def draw(self, wxdc: wx.PaintDC):
        if self.open_pen is None:
            self.open_pen = wx.Pen((200, 0, 0))
        if self.close_pen is None:
            self.close_pen = wx.Pen((0, 0, 200))

        wxdc.SetBrush(wx.TRANSPARENT_BRUSH)
        pens = [self.open_pen if is_open else self.close_pen for v in self.group_by_size.values() for is_open in v["is_open"]]
        wxdc.SetLogicalOrigin(self.xoffset * -1, 0)
        wxdc.DrawRectangleList(self.draw_rects, pens)
        wxdc.SetLogicalOrigin(0, 0)

    def __getitem__(self, key):
        hole_size, idx = self.group_by_name[key]
        ret = {
            "pos": self.group_by_size[hole_size]["pos"][idx],
            "is_open": self.group_by_size[hole_size]["is_open"][idx],
            "to_open": self.group_by_size[hole_size]["to_open"][idx],
            "to_close": self.group_by_size[hole_size]["to_close"][idx],
        }
        return ret


class BasePlayer:
    def __init__(self, confpath, midiobj: MidiWrap):
        self.midi = midiobj

        # load tracker config
        with open(confpath, encoding="utf-8") as f:
            conf = json.load(f)

        self.manual_expression = False
        self.stack_split = conf["expression"]["stack_split_point"] - conf["tracker_holes"]["lowest_note"]
        self.treble_vacuum = self.bass_vacuum = conf["expression"].get("vacuum", 6)
        self.spool_diameter = conf["spool_diameter"]
        self.roll_width = conf["roll_width"]
        self.default_tempo = conf["default_tempo"]
        self.is_dark_hole = conf["tracker_holes"]["is_dark_hole"]
        self.on_bright = conf["tracker_holes"]["on_brightness"]

        self.holes = TrackerHoles(conf)
        self.during_emulate_evt = threading.Event()
        self.during_emulate_evt.set()

        self.tracker_offset = 0
        self.auto_tracking = True
        self.emulate_enable = False

        # vacuum to velocity map
        self.max_vacuum = 40
        vacuum = list(range(4, self.max_vacuum + 1))
        self.velocity = [33, 37, 42, 46.5, 50.5, 54, 57, 59.5, 61.7, 63.7, 65.5, 67.1, 68.6, 70, 71.3, 72.5, 73.6, 74.6, 75.6, 76.5, 77.4, 78.3, 79.1, 79.9, 80.7, 81.4, 82.1, 82.8, 83.4, 84, 84.6, 85.2, 85.8, 86.4, 87, 87.6, 88.2]
        k = np.polyfit(self.velocity, vacuum, 5)
        self.velocity_bins = [np.poly1d(k)(v) for v in range(int(self.velocity[0]), int(self.velocity[-1] + 1))]

        # for manual expression by keyboard input
        self.bass_accent = False
        self.bass_accent_key = ord("A")
        self.treble_accent = False
        self.treble_accent_key = ord("S")
        self.manual_exp_map = {
            ord("J"): {"press": False, "vacuum": 3},
            ord("K"): {"press": False, "vacuum": 7},
            ord("L"): {"press": False, "vacuum": 15},
        }

    def calc_velocity(self):
        idx = np.digitize([self.bass_vacuum, self.treble_vacuum], bins=self.velocity_bins)
        return self.velocity[0] + idx

    def emulate_off(self):
        self.emulate_enable = False
        self.during_emulate_evt.wait(timeout=1)
        self.holes.all_off()
        self.midi.all_off()

    def emulate_on(self):
        self.emulate_enable = True

    def auto_track(self, frame):
        if not self.auto_tracking:
            return

        # find roll edge
        roi = np.array([frame[250:350:5, 0:7], frame[250:350:5, 793:800]])
        if self.is_dark_hole:
            left_end, right_end = (roi > self.on_bright).all(axis=3).sum(axis=2).mean(axis=1)
        else:
            left_end, right_end = (roi <= self.on_bright).all(axis=3).sum(axis=2).mean(axis=1)

        self.tracker_offset = int(right_end - left_end)

    def emulate(self, frame, curtime):
        if self.emulate_enable:
            self.during_emulate_evt.clear()

            self.auto_track(frame)
            self.holes.set_frame(frame, self.tracker_offset)
            self.emulate_expression(curtime)
            self.emulate_manual_expression(curtime)
            self.emulate_pedals()
            self.emulate_notes()

            self.during_emulate_evt.set()

    def expression_key_event(self, key: int, pressed: bool) -> None:
        if key == self.bass_accent_key:
            self.bass_accent = pressed

        if key == self.treble_accent_key:
            self.treble_accent = pressed

        accomp_map = self.manual_exp_map.get(key, None)
        if accomp_map is not None:
            if accomp_map["press"] and not pressed:
                accomp_map["press"] = False
            if not accomp_map["press"] and pressed:
                accomp_map["press"] = True

    def emulate_expression(self, curtime):
        pass

    def emulate_manual_expression(self, curtime):
        if not self.manual_expression:
            return

        # override manual expression
        accomp_vacuum = 6 + sum([v["vacuum"] for v in self.manual_exp_map.values() if v["press"]])
        self.bass_vacuum = self.treble_vacuum = accomp_vacuum

        if self.bass_accent:
            self.bass_vacuum = min(self.bass_vacuum + 6, self.max_vacuum)

        if self.treble_accent:
            self.treble_vacuum = min(self.treble_vacuum + 6, self.max_vacuum)

    def emulate_pedals(self):
        # sustain pedal
        sustain = self.holes["sustain"]
        if sustain["to_open"]:
            self.midi.sustain_on()

        elif sustain["to_close"]:
            self.midi.sustain_off()

        # hammer rail lift emulation
        soft = self.holes["soft"]
        if soft["to_open"]:
            self.midi.hammer_lift_on()

        elif soft["to_close"]:
            self.midi.hammer_lift_off()

    def emulate_notes(self):
        note = self.holes["note"]
        offset = self.holes.lowest_note + 21

        on_notes = note["to_open"].nonzero()[0]
        if on_notes.size > 0:
            bass_velo, treble_velo = self.calc_velocity()
            for key in on_notes:
                velo = bass_velo if key < self.stack_split else treble_velo
                self.midi.note_on(key + offset, velo)

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset)

    def draw_tracker(self, wxdc: wx.PaintDC):
        # draw tracker frame
        wxdc.SetPen(wx.Pen((0, 100, 100)))
        wxdc.DrawLineList([(0, 275, 799, 275), (0, 325, 799, 325)])

        # draw tracker ear
        wxdc.SetPen(wx.Pen((200, 0, 0)))
        wxdc.DrawLineList([(6, 290, 6, 310), (793, 290, 793, 310)])

        # draw holes
        self.holes.draw(wxdc)


if __name__ == "__main__":
    import os
    import time

    midiobj = MidiWrap()
    player = BasePlayer(os.path.join("playsk_config", "88 Note white back.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    player.emulate_on()
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
