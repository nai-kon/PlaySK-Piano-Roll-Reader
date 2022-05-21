import numpy as np
from player import Player


class AmpicoB(Player):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.amp_lock_pos = 0
        self.cres_pos = 0
        self.slow_cres_sec = 4
        self.fast_cres_sec = 0.9
        self.pre_time = None

        self.bass_intensity_lock = [False, False, False]  # 2->4->6
        self.treble_intensity_lock = [False, False, False]  # 2->4->6
        self.bass_sub_intensity_lock = False
        self.treble_sub_intensity_lock = False

        # vacuum range of no-amplifier to 2nd amplifier
        self.intensity_range = {
            "none-sub": [5.0, 10.0],
            "none": [5.6, 11.35],
            "2-sub": [5.6, 11.6],
            "2": [6.6, 13.1],
            "4-sub": [6.25, 13.8],
            "4": [7.9, 15.8],
            "24-sub": [7.75, 15.7],
            "24": [9.0, 16.8],
            "6-sub": [8.7, 16.5],
            "6": [9.8, 19.5],
            "26-sub": [10.65, 21],
            "26": [12.4, 24.6],
            "46-sub": [13.8, 28],
            "46": [15.6, 31.7],
            "246-sub": [18.6, 36],
            "246": [19.6, 40],
        }

        self.bass_vacuum = self.intensity_range["none"][0]
        self.treble_vacuum = self.intensity_range["none"][0]

    def emulate_off(self):
        super().emulate_off()
        self.bass_intensity_lock = [False, False, False]
        self.treble_intensity_lock = [False, False, False]
        self.bass_sub_intensity_lock = False
        self.treble_sub_intensity_lock = False
        self.amp_lock_pos = 0
        self.cres_pos = 0
        self.bass_vacuum = self.intensity_range["none"][0]
        self.treble_vacuum = self.intensity_range["none"][0]

    def emulate_expression(self, frame, curtime):
        bass_cancel = self.holes["bass_cancel"]
        treble_cancel = self.holes["treble_cancel"]
        bass_intensities = self.holes["bass_intensity"]  # [2, 4, 6]
        treble_intensities = self.holes["treble_intensity"]  # [6, 4, 2]
        sub_intensity = self.holes["subintensity"]

        # cancel intensity
        if bass_cancel["is_open"]:
            # print("bass cancel")
            self.bass_intensity_lock[:] = [False, False, False]
            self.bass_sub_intensity_lock = False

        if treble_cancel["is_open"]:
            # print("treble cancel")
            self.treble_intensity_lock[:] = [False, False, False]
            self.treble_sub_intensity_lock = False

        if sub_intensity["is_open"]:
            # print("sub-zero intensity triggered")
            self.treble_sub_intensity_lock = True
            self.bass_sub_intensity_lock = True

        # triger intensity holes
        if bass_intensities["is_open"][0]:  # bass lv 2
            self.bass_intensity_lock[0] = True
        if bass_intensities["is_open"][1]:  # bass lv 4
            self.bass_intensity_lock[1] = True
        if bass_intensities["is_open"][2]:  # bass lv 6
            self.bass_intensity_lock[2] = True

        if treble_intensities["is_open"][2]:  # treble lv 2
            self.treble_intensity_lock[0] = True
        if treble_intensities["is_open"][1]:  # treble lv 4
            self.treble_intensity_lock[1] = True
        if treble_intensities["is_open"][0]:  # treble lv 6
            self.treble_intensity_lock[2] = True

        self.calc_crescendo(curtime)
        self.calc_bass_expression()
        self.calc_treble_expression()

    def calc_crescendo(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime

        amplifier = self.holes["amplifier"]
        slow_cres = self.holes["treble_slow_cresc"]
        fast_cres = self.holes["treble_fast_cresc"]

        # amplifier operation
        if amplifier["to_open"]:
            if not slow_cres["is_open"]:
                if self.amp_lock_pos == 1:
                    self.amp_lock_pos = 0.4  # 1st amplifier
                elif self.amp_lock_pos == 0.4:
                    self.amp_lock_pos = 0  # none amplifier
        elif amplifier["to_close"]:
            if slow_cres["is_open"]:
                if self.amp_lock_pos == 0:
                    self.amp_lock_pos = 0.4  # 1st amplifier
                elif self.amp_lock_pos == 0.4:
                    self.amp_lock_pos = 1.0  # 2nd amplifier

        if slow_cres["is_open"]:
            if fast_cres["is_open"] or amplifier["is_open"]:
                # fast crescendo
                self.cres_pos += (curtime - self.pre_time) * (1 / self.fast_cres_sec)
            else:
                # slow crescendo
                self.cres_pos += (curtime - self.pre_time) * (1 / self.slow_cres_sec)

        else:
            if fast_cres["is_open"] or amplifier["is_open"]:
                # fast decrescendo
                self.cres_pos -= (curtime - self.pre_time) * (1 / self.fast_cres_sec)
                self.cres_pos = max(self.cres_pos, self.amp_lock_pos)  # amplifire lock
            else:
                # slow decrescendo
                self.cres_pos -= (curtime - self.pre_time) * (1 / self.slow_cres_sec)
                self.cres_pos = max(self.cres_pos, self.amp_lock_pos)  # amplifire lock

        self.cres_pos = max(self.cres_pos, 0)
        self.cres_pos = min(self.cres_pos, 1)

        self.pre_time = curtime

    def calc_bass_expression(self):

        opcode = ""
        if not any(self.bass_intensity_lock):
            opcode = "none"
        if self.bass_intensity_lock[0]:
            opcode += "2"
        if self.bass_intensity_lock[1]:
            opcode += "4"
        if self.bass_intensity_lock[2]:
            opcode += "6"
        if self.bass_sub_intensity_lock:
            opcode += "-sub"

        min, max = self.intensity_range.get(opcode, [10, 20])
        self.bass_vacuum = min + self.cres_pos * (max - min)

    def calc_treble_expression(self):

        opcode = ""
        if not any(self.treble_intensity_lock):
            opcode = "none"
        if self.treble_intensity_lock[0]:
            opcode += "2"
        if self.treble_intensity_lock[1]:
            opcode += "4"
        if self.treble_intensity_lock[2]:
            opcode += "6"
        if self.treble_sub_intensity_lock:
            opcode += "-sub"

        min, max = self.intensity_range.get(opcode, [10, 20])

        self.treble_vacuum = min + self.cres_pos * (max - min)

    def draw_tracker(self, frame):
        # need override for drawing intensity lock
        self.holes["bass_intensity"]["is_open"][:] = self.bass_intensity_lock[:]
        self.holes["treble_intensity"]["is_open"][:] = self.treble_intensity_lock[::-1]
        self.holes["subintensity"]["is_open"][0] = self.bass_sub_intensity_lock or self.treble_sub_intensity_lock
        super().draw_tracker(frame)


if __name__ == "__main__":
    import time
    import os
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = AmpicoB(os.path.join("config", "Ampico B white background.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
