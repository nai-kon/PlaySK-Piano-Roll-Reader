import cv2
import json
import numpy as np


class TrackerHoles():
    def __init__(self, conf):

        holes = conf["tracker_holes"]
        self.is_dark_hole = holes["is_dark_hole"]
        self.th_bright = holes["on_brightness"]
        self.lowest_note = holes["lowest_note"]

        # use numpy for fast hole open/close calculation
        self.holes_bysize = {}
        self.holes_byname = {}
        for name, v in holes.items():
            if isinstance(v, dict) and "w" in v:
                key = (v["w"], v["h"])
                self.holes_bysize.setdefault(key, {"pos": [], "on_apatures": [], "off_apatures": []})
                si = len(self.holes_bysize[key]["pos"])

                xs = v["x"] if isinstance(v["x"], list) else [v["x"]]
                tmp = [(x, v["y"], x + v["w"], v["y"] + v["h"]) for x in xs]
                self.holes_bysize[key]["pos"].extend(tmp)
                tmp = [v["on_apature"]] * len(xs)
                self.holes_bysize[key]["on_apatures"].extend(tmp)
                tmp = [v["off_apature"]] * len(xs)
                self.holes_bysize[key]["off_apatures"].extend(tmp)

                ei = len(self.holes_bysize[key]["pos"])
                self.holes_byname.setdefault(name, [key, slice(si, ei)])

        for v in self.holes_bysize.values():
            v["is_open"] = v["to_open"] = v["to_close"] = np.array([False] * len(v["pos"]))
            v["on_apatures"] = np.array(v["on_apatures"])
            v["off_apatures"] = np.array(v["off_apatures"])

        self.xoffset = 0

    def setframe(self, frame, xoffset):
        self.xoffset = xoffset

        # calc hole open ratio
        for size, v in self.holes_bysize.items():
            hole_list = np.array([frame[p[1]: p[3], p[0] + xoffset: p[2] + xoffset] for p in v["pos"]])

            if self.is_dark_hole:
                open_ratios = (hole_list < self.th_bright).all(axis=3).mean(axis=(2, 1))
                # open_ratios = (hole_list < self.th_bright).mean(axis=(3, 2, 1))
            else:
                open_ratios = (hole_list > self.th_bright).all(axis=3).mean(axis=(2, 1))
                # open_ratios = (hole_list > self.th_bright).mean(axis=(3, 2, 1))

            v["to_open"] = (~v["is_open"]) & (open_ratios > v["on_apatures"])  # hole is opened just now
            v["to_close"] = v["is_open"] & (open_ratios < v["off_apatures"])  # hole is closed just now
            v["is_open"] ^= (v["to_open"] | v["to_close"])  # hole is open or close

    def all_off(self):
        for v in self.holes_bysize.values():
            v["is_open"] = v["to_open"] = v["to_close"] = np.array([False] * len(v["pos"]))

    def draw(self, frame):
        for v in self.holes_bysize.values():
            for pos, open in zip(v["pos"], v["is_open"]):
                color = (200, 0, 0) if open else (0, 0, 200)
                cv2.rectangle(frame, (pos[0] + self.xoffset, pos[1]), (pos[2] + self.xoffset, pos[3]), color, 1)

    def __getitem__(self, key):
        holesize, idx = self.holes_byname[key]

        ret = {
            "pos": self.holes_bysize[holesize]["pos"][idx],
            "is_open": self.holes_bysize[holesize]["is_open"][idx],
            "to_open": self.holes_bysize[holesize]["to_open"][idx],
            "to_close": self.holes_bysize[holesize]["to_close"][idx],
        }
        return ret


class Player():
    def __init__(self, confpath, midiobj):
        self.midiobj = midiobj

        # load tracker config
        with open(confpath, encoding="utf-8") as f:
            conf = json.load(f)

        self.stack_split = conf["expression"]["stack_split_point"] - conf["tracker_holes"]["lowest_note"]
        self.treble_vacuum = self.bass_vacuum = conf["expression"]["vacuum"]
        self.spool_diameter = conf["spool"]["diameter"]
        self.is_dark_hole = conf["tracker_holes"]["is_dark_hole"]
        self.on_bright = conf["tracker_holes"]["on_brightness"]

        self.holes = TrackerHoles(conf)

        self.tracker_offset = 0
        self.auto_tracking = True
        self.emulate_enable = True

        # vacuum to velocity map
        vac = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40]
        self.velo = [35, 41, 46, 50.5, 54, 57, 59.5, 61.7, 63.7, 65.5, 67.1, 68.6, 70, 71.3, 72.5, 73.6, 74.6, 75.6, 76.5, 77.4, 78.3, 79.1, 79.9, 80.7, 81.4, 82.1, 82.8, 83.4, 84, 84.6, 85.2, 85.8, 86.4, 87, 87.6, 88.2]
        k = np.polyfit(self.velo, vac, 5)
        self.velo_bins = [np.poly1d(k)(v) for v in range(int(self.velo[0]), int(self.velo[-1] + 1))]

    def calc_velo(self):
        idx = np.digitize([self.bass_vacuum, self.treble_vacuum], bins=self.velo_bins)
        return self.velo[0] + idx

    def emulate_off(self):
        self.emulate_enable = False
        self.holes.all_off()
        self.midiobj.all_off()

    def emulate_on(self):
        self.emulate_enable = True

    def set_tracker_offset(self, offset):
        self.tracker_offset = offset

    def get_tracker_offset(self):
        return self.tracker_offset

    def set_auto_tracking(self, val):
        self.auto_tracking = val

    def auto_track(self, frame):
        if not self.auto_tracking:
            return

        # find roll edge
        roi = np.array([frame[250:350:5, 0:7], frame[250:350:5, 793:800]])
        if self.is_dark_hole:
            leftedge, rightedge = (roi < self.on_bright).all(axis=3).sum(axis=2).mean(axis=1)
        else:
            leftedge, rightedge = (roi > self.on_bright).all(axis=3).sum(axis=2).mean(axis=1)

        self.tracker_offset = int(leftedge - rightedge) + 1

    def emulate(self, frame, curtime):

        if self.emulate_enable:
            self.auto_track(frame)
            self.holes.setframe(frame, self.tracker_offset)
            self.emulate_expression(frame, curtime)
            self.emulate_pedals(frame)
            self.emulate_notes(frame)

        self.draw_tracker(frame)

    def emulate_expression(self, frame, curtime):
        pass

    def emulate_pedals(self, frame):
        # sustain pedal
        sustain = self.holes["sustain"]
        if sustain["to_open"]:
            self.midiobj.sustain_on()

        elif sustain["to_close"]:
            self.midiobj.sustain_off()

        # hammer rail lift emulation
        soft = self.holes["soft"]
        if soft["to_open"]:
            self.midiobj.hammer_lift_on()

        elif soft["to_close"]:
            self.midiobj.hammer_lift_off()

    def emulate_notes(self, frame):

        b_velo, t_velo = self.calc_velo()
        note = self.holes["note"]
        offset = self.holes.lowest_note + 21

        for key, val in enumerate(zip(note["to_open"], note["to_close"])):
            velo = b_velo if key < self.stack_split else t_velo
            if val[0]:
                self.midiobj.note_on(key + offset, velo)

            elif val[1]:
                self.midiobj.note_off(key + offset)

    def draw_tracker(self, frame):

        # tracker frame
        cv2.line(frame, (0, 275), (799, 275), (0, 100, 100), 1, cv2.LINE_4)
        cv2.line(frame, (0, 325), (799, 325), (0, 100, 100), 1, cv2.LINE_4)

        # tracker ear
        cv2.line(frame, (6, 290), (6, 310), (200, 0, 0), 1, cv2.LINE_4)
        cv2.line(frame, (793, 290), (793, 310), (200, 0, 0), 1, cv2.LINE_4)

        # holes
        self.holes.draw(frame)


if __name__ == "__main__":
    import time
    import os
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = Player(os.path.join("config", "88Note white background.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
