import wx

from .base_player import BasePlayer


class AmpicoA(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.amplifier_pos = 0
        self.full_amplifier_time = 0.5  # 0.5 sec to full collapse

        # intensities (W.G) with amplifier 0% and 100%
        self.intensity_range = {
            "none": [6.0, 7.0],
            "2": [6.7, 8.0],
            "4": [8.0, 9.5],
            "24": [9.5, 11.5],
            "6": [10.5, 13.0],
            "26": [13.0, 16.5],
            "46": [16.5, 25.5],
            "246": [20.0, 30.0],
        }
        self.min_vacuum = self.intensity_range["none"][0]
        self.max_vacuum = self.intensity_range["246"][1]

        # crescendo increase rates (W.G) of each intensities.
        self.bass_crescendo_pos = self.min_vacuum
        self.treble_crescendo_pos = self.min_vacuum
        self.crescendo_rates = {
            "none": 3.5,
            "2": 3.9,
            "4": 5.0,
            "24": 6.0,
            "6": 6.0,
            "26": 6.5,
            "46": 7.0,
            "246": 7.0,
            "fast": 12,
        }

        self.pre_time = None
        self.bass_intensity_lock = [False, False, False]  # 2->4->6
        self.treble_intensity_lock = [False, False, False]  # 2->4->6

        self.delay_ratio = 0.6
        self.bass_vacuum = self.treble_vacuum = self.intensity_range["none"][0]
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.intensity_range["none"][0]

    def emulate_off(self):
        super().emulate_off()
        self.bass_intensity_lock = [False, False, False]
        self.treble_intensity_lock = [False, False, False]
        self.amplifier_pos = 0
        self.bass_crescendo_pos = self.min_vacuum
        self.treble_crescendo_pos = self.min_vacuum
        self.bass_vacuum = self.treble_vacuum = self.intensity_range["none"][0]
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.intensity_range["none"][0]

    def emulate_expression(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime
        delta_time = curtime - self.pre_time

        bass_cancel = self.holes["bass_cancel"]
        treble_cancel = self.holes["treble_cancel"]
        bass_intensities = self.holes["bass_intensity"]  # [2, 4, 6]
        treble_intensities = self.holes["treble_intensity"]  # [6, 4, 2]

        # cancel intensity
        if bass_cancel["is_open"]:
            self.bass_intensity_lock[:] = [False, False, False]
            self.bass_sub_intensity_lock = False

        if treble_cancel["is_open"]:
            self.treble_intensity_lock[:] = [False, False, False]
            self.treble_sub_intensity_lock = False

        # trigger intensity holes (LV2->4->6)
        for idx in range(3):
            # bass 2->4->6
            if bass_intensities["is_open"][idx]:
                self.bass_intensity_lock[idx] = True
            # treble 2->4->6
            if treble_intensities["is_open"][2 - idx]:
                self.treble_intensity_lock[idx] = True

        self.calc_amplifier(delta_time)
        self.calc_expression(delta_time)
        self.pre_time = curtime

    def calc_amplifier(self, delta_time):
        # treble/bass intensity 6 hole triggers amplifier
        if self.bass_intensity_lock[2] or self.treble_intensity_lock[2]:
            self.amplifier_pos += delta_time / self.full_amplifier_time
        else:
            self.amplifier_pos -= delta_time / self.full_amplifier_time

        if self.bass_intensity_lock == [True, True, True] or \
            self.treble_intensity_lock == [True, True, True]:
            # amplifier will 100% with 2&4&6 open.
            self.amplifier_pos = min(self.amplifier_pos, 1.0)
        elif self.bass_intensity_lock == [True, False, True] or \
            self.treble_intensity_lock == [True, False, True]:
            # 50% with 2&6 open.
            self.amplifier_pos = min(self.amplifier_pos, 0.5)
        elif self.bass_intensity_lock == [False, False, True] or \
            self.treble_intensity_lock == [False, False, True]:
            # 20% with 6 open.
            self.amplifier_pos = min(self.amplifier_pos, 0.2)

        self.amplifier_pos = max(self.amplifier_pos, 0)
        self.amplifier_pos = min(self.amplifier_pos, 1)

    def calc_expression(self, delta_time):
        def calc_vacuum(intensity_lock):
            opcode = ""
            if not any(intensity_lock):
                opcode = "none"
            if intensity_lock[0]:
                opcode += "2"
            if intensity_lock[1]:
                opcode += "4"
            if intensity_lock[2]:
                opcode += "6"

            vac_min, vac_max = self.intensity_range.get(opcode, [10, 20])
            return vac_min + self.amplifier_pos * (vac_max - vac_min), opcode

        # bass vacuum
        bass_vacuum, bass_opcode = calc_vacuum(self.bass_intensity_lock)
        if self.holes["bass_fast_cresc"]["is_open"]:
            bass_opcode = "fast"
        if self.holes["bass_slow_cresc"]["is_open"]:
            cres_rate = self.crescendo_rates[bass_opcode] * delta_time
        else:
            cres_rate = self.crescendo_rates[bass_opcode] * delta_time * -1
        self.bass_crescendo_pos += cres_rate
        self.bass_crescendo_pos = min(self.bass_crescendo_pos, self.max_vacuum)
        self.bass_crescendo_pos = max(self.bass_crescendo_pos, self.min_vacuum)
        # combine crescendo and intensity
        bass_target_vac = self.bass_crescendo_pos + bass_vacuum - self.min_vacuum
        bass_target_vac = min(bass_target_vac, self.max_vacuum)

        # treble vacuum
        treble_vacuum, treble_opcode = calc_vacuum(self.treble_intensity_lock)
        if self.holes["treble_fast_cresc"]["is_open"]:
            treble_opcode = "fast"
        if self.holes["treble_slow_cresc"]["is_open"]:
            cres_rate = self.crescendo_rates[treble_opcode] * delta_time
        else:
            cres_rate = self.crescendo_rates[treble_opcode] * delta_time * -1
        self.treble_crescendo_pos += cres_rate
        self.treble_crescendo_pos = min(self.treble_crescendo_pos, self.max_vacuum)
        self.treble_crescendo_pos = max(self.treble_crescendo_pos, self.min_vacuum)
        # combine crescendo and intensity
        treble_target_vac = self.treble_crescendo_pos + treble_vacuum - self.min_vacuum
        treble_target_vac = min(treble_target_vac, self.max_vacuum)

        # delay function
        self.bass_vacuum = self.bass_vacuum_pre + (bass_target_vac - self.bass_vacuum_pre) * self.delay_ratio
        self.treble_vacuum = self.treble_vacuum_pre + (treble_target_vac - self.treble_vacuum_pre) * self.delay_ratio
        self.bass_vacuum_pre = self.bass_vacuum
        self.treble_vacuum_pre = self.treble_vacuum

    def draw_tracker(self, wxdc: wx.PaintDC):
        # need override for drawing intensity lock
        self.holes["bass_intensity"]["is_open"][:] = self.bass_intensity_lock[:]
        self.holes["treble_intensity"]["is_open"][:] = self.treble_intensity_lock[::-1]
        super().draw_tracker(wxdc)


if __name__ == "__main__":
    import os
    import time

    import numpy as np
    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = AmpicoA(os.path.join("playsk_config", "Ampico A white back.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
