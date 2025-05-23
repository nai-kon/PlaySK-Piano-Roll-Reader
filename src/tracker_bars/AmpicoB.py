import wx

from .base_player import BasePlayer


class AmpicoB(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.amp_lock_range = [0, 1.0]
        self.amp_cres_pos = 0
        self.slow_cres_rate = 1 / 4  # 4sec
        self.fast_cres_rate = 1 / 0.8  # 0.8sec
        self.pre_time = None

        self.bass_intensity_lock = [False, False, False]  # 2->4->6
        self.treble_intensity_lock = [False, False, False]  # 2->4->6
        self.bass_sub_intensity_lock = False
        self.treble_sub_intensity_lock = False

        # vacuum range (W.G) of no amplifier to 2nd amplifier
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

        self.delay_ratio = 0.6
        self.bass_vacuum = self.treble_vacuum = self.intensity_range["none"][0]
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.intensity_range["none"][0]

    def emulate_off(self):
        super().emulate_off()
        self.bass_intensity_lock = [False, False, False]
        self.treble_intensity_lock = [False, False, False]
        self.bass_sub_intensity_lock = False
        self.treble_sub_intensity_lock = False
        self.amp_lock_range = [0, 1.0]
        self.amp_cres_pos = 0
        self.bass_vacuum = self.treble_vacuum = self.intensity_range["none"][0]
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.intensity_range["none"][0]

    def emulate_expression(self, curtime):
        bass_cancel = self.holes["bass_cancel"]
        treble_cancel = self.holes["treble_cancel"]
        bass_intensities = self.holes["bass_intensity"]  # [2, 4, 6]
        treble_intensities = self.holes["treble_intensity"]  # [6, 4, 2]
        sub_intensity = self.holes["subintensity"]

        # cancel intensity
        if bass_cancel["is_open"]:
            self.bass_intensity_lock[:] = [False, False, False]
            self.bass_sub_intensity_lock = False

        if treble_cancel["is_open"]:
            self.treble_intensity_lock[:] = [False, False, False]
            self.treble_sub_intensity_lock = False

        if sub_intensity["is_open"]:
            self.treble_sub_intensity_lock = True
            self.bass_sub_intensity_lock = True

        # trigger intensity holes (LV2->4->6)
        for idx in range(3):
            # bass 2->4->6
            if bass_intensities["is_open"][idx]:
                self.bass_intensity_lock[idx] = True
            # treble 2->4->6
            if treble_intensities["is_open"][2 - idx]:
                self.treble_intensity_lock[idx] = True


        self.calc_crescendo(curtime)
        self.calc_expression()

    def calc_crescendo(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime
        delta_time = curtime - self.pre_time

        amplifier = self.holes["amplifier"]
        slow_cres = self.holes["treble_slow_cresc"]
        fast_cres = self.holes["treble_fast_cresc"]

        if amplifier["to_close"] and 0.3 < self.amp_cres_pos < 0.85:
            self.amp_lock_range = [0.3, 0.85]  # 1st amplifier
        elif amplifier["to_close"] and 0.85 < self.amp_cres_pos:
            self.amp_lock_range = [0.85, 1.0]  # 2nd amplifier
        elif (amplifier["to_close"] and self.amp_cres_pos < 0.3) or amplifier["to_open"]:
            self.amp_lock_range = [0, 1.0]

        if slow_cres["is_open"]:
            if fast_cres["is_open"] or amplifier["is_open"]:
                # fast crescendo
                self.amp_cres_pos += delta_time * self.fast_cres_rate
            else:
                # slow crescendo
                self.amp_cres_pos += delta_time * self.slow_cres_rate

        else:
            if fast_cres["is_open"] or amplifier["is_open"]:
                # fast decrescendo
                self.amp_cres_pos -= delta_time * self.fast_cres_rate
            else:
                # slow decrescendo
                self.amp_cres_pos -= delta_time * self.slow_cres_rate

        self.amp_cres_pos = max(self.amp_cres_pos, self.amp_lock_range[0])
        self.amp_cres_pos = min(self.amp_cres_pos, self.amp_lock_range[1])

        self.pre_time = curtime

    def calc_expression(self):
        def calc_vacuum(intensity_lock, sub_intensity_lock):
            opcode = ""
            if not any(intensity_lock):
                opcode = "none"
            if intensity_lock[0]:
                opcode += "2"
            if intensity_lock[1]:
                opcode += "4"
            if intensity_lock[2]:
                opcode += "6"
            if sub_intensity_lock:
                opcode += "-sub"

            vac_min, vac_max = self.intensity_range.get(opcode, [10, 20])
            return vac_min + self.amp_cres_pos * (vac_max - vac_min)

        bass_target_vac = calc_vacuum(self.bass_intensity_lock, self.bass_sub_intensity_lock)
        treble_target_vac = calc_vacuum(self.treble_intensity_lock, self.treble_sub_intensity_lock)

        # delay function
        self.bass_vacuum = self.bass_vacuum_pre + (bass_target_vac - self.bass_vacuum_pre) * self.delay_ratio
        self.treble_vacuum = self.treble_vacuum_pre + (treble_target_vac - self.treble_vacuum_pre) * self.delay_ratio
        self.bass_vacuum_pre = self.bass_vacuum
        self.treble_vacuum_pre = self.treble_vacuum

    def draw_tracker(self, wxdc: wx.PaintDC):
        # need override for drawing intensity lock
        self.holes["bass_intensity"]["is_open"][:] = self.bass_intensity_lock[:]
        self.holes["treble_intensity"]["is_open"][:] = self.treble_intensity_lock[::-1]
        self.holes["subintensity"]["is_open"][0] = self.bass_sub_intensity_lock or self.treble_sub_intensity_lock
        super().draw_tracker(wxdc)


if __name__ == "__main__":
    import os
    import time

    import numpy as np

    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = AmpicoB(os.path.join("playsk_config", "Ampico B.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
