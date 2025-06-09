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
            "46": [16.5, 22.0],
            "246": [20.0, 30.0],
        }
        self.min_vacuum = self.intensity_range["none"][0]
        self.max_vacuum = self.intensity_range["246"][1]

        # crescendo vacuum increase rates per sec of each intensities.
        self.bass_crescendo_vacuum = self.min_vacuum
        self.treble_crescendo_vacuum = self.min_vacuum
        self.crescendo_rates = {
            "none": 3,  # 8sec to max
            "2": 3.5,
            "4": 4.5,
            "24": 5.5,
            "6": 5.5,
            "26": 6.0,
            "46": 6.5,
            "246": 6.5,
            "fast": 12,  # 2sec to max
        }

        self.bass_vacuum = self.treble_vacuum = self.min_vacuum
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.min_vacuum
        self.delay_ratio = 0.6

        self.pre_time = None
        self.bass_intensity_lock = [False, False, False]  # 2->4->6
        self.treble_intensity_lock = [False, False, False]  # 2->4->6

        self.evalve_control_holes = {
            "bass_slow_cresc": {"midi_no": 16},
            "bass_intensity": {"midi_no": [17, 19, 21]},
            "sustain": {"midi_no": 18},
            "bass_fast_cresc": {"midi_no": 20},
            "bass_cancel": {"midi_no": 22},
            "treble_cancel": {"midi_no": 107},
            "treble_intensity": {"midi_no": [108, 110, 112]},
            "treble_fast_cresc": {"midi_no": 109},
            "soft": {"midi_no": 111},
            "treble_slow_cresc": {"midi_no": 113},
        }

    def emulate_off(self):
        super().emulate_off()
        self.bass_intensity_lock = [False, False, False]
        self.treble_intensity_lock = [False, False, False]
        self.amplifier_pos = 0
        self.bass_crescendo_vacuum = self.min_vacuum
        self.treble_crescendo_vacuum = self.min_vacuum
        self.bass_vacuum = self.treble_vacuum = self.min_vacuum
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.min_vacuum

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

        if treble_cancel["is_open"]:
            self.treble_intensity_lock[:] = [False, False, False]

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
        # intensity triggers amplifier
        target_amp_pos = 0
        if self.bass_intensity_lock[1] and self.bass_intensity_lock[2] or \
            self.treble_intensity_lock[1] and self.treble_intensity_lock[2]:
            # amplifier will 100% with 4&6 open.
            target_amp_pos = 1.0
        elif self.bass_intensity_lock[0] and self.bass_intensity_lock[2] or \
            self.treble_intensity_lock[0] and self.treble_intensity_lock[2]:
            # 50% with 2&6 open.
            target_amp_pos = 0.5
        elif self.bass_intensity_lock[2] or \
            self.treble_intensity_lock[2]:
            # 20% with 6 open.
            target_amp_pos = 0.2

        # also stack vacuum (crescendo) triggers amplifier
        # begin to amplify at 15 inches
        stack_vacuum = max(self.bass_vacuum, self.treble_vacuum)
        target_amp_pos2 = max(((stack_vacuum - 15) / 15), 0)

        # calc delta amplifier position
        delta_amp_pos = delta_time / self.full_amplifier_time
        target_amp_pos = max(target_amp_pos, target_amp_pos2)
        if self.amplifier_pos < target_amp_pos:
            self.amplifier_pos += delta_amp_pos
            self.amplifier_pos = min(self.amplifier_pos, target_amp_pos)
        else:
            self.amplifier_pos -= delta_amp_pos
            self.amplifier_pos = max(self.amplifier_pos, target_amp_pos)

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
        self.bass_crescendo_vacuum += cres_rate
        self.bass_crescendo_vacuum = min(self.bass_crescendo_vacuum, self.max_vacuum)
        self.bass_crescendo_vacuum = max(self.bass_crescendo_vacuum, self.min_vacuum)
        # combine crescendo and intensity
        bass_target_vac = self.bass_crescendo_vacuum + bass_vacuum - self.min_vacuum
        bass_target_vac = min(bass_target_vac, self.max_vacuum)

        # treble vacuum
        treble_vacuum, treble_opcode = calc_vacuum(self.treble_intensity_lock)
        if self.holes["treble_fast_cresc"]["is_open"]:
            treble_opcode = "fast"
        if self.holes["treble_slow_cresc"]["is_open"]:
            cres_rate = self.crescendo_rates[treble_opcode] * delta_time
        else:
            cres_rate = self.crescendo_rates[treble_opcode] * delta_time * -1
        self.treble_crescendo_vacuum += cres_rate
        self.treble_crescendo_vacuum = min(self.treble_crescendo_vacuum, self.max_vacuum)
        self.treble_crescendo_vacuum = max(self.treble_crescendo_vacuum, self.min_vacuum)
        # combine crescendo and intensity
        treble_target_vac = self.treble_crescendo_vacuum + treble_vacuum - self.min_vacuum
        treble_target_vac = min(treble_target_vac, self.max_vacuum)

        # delay function
        self.bass_vacuum = self.bass_vacuum_pre + (bass_target_vac - self.bass_vacuum_pre) * self.delay_ratio
        self.treble_vacuum = self.treble_vacuum_pre + (treble_target_vac - self.treble_vacuum_pre) * self.delay_ratio
        self.bass_vacuum_pre = self.bass_vacuum
        self.treble_vacuum_pre = self.treble_vacuum

    def draw_tracker(self, wxdc: wx.PaintDC):
        super().draw_tracker(wxdc)
        # overdraw lock & cancel holes
        for idx in range(3):
            self.holes.draw(wxdc, self.bass_intensity_lock[idx], "bass_intensity", idx)
            self.holes.draw(wxdc, self.treble_intensity_lock[idx], "treble_intensity", 2 - idx)

if __name__ == "__main__":
    import os
    import time

    import numpy as np

    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = AmpicoA(os.path.join("playsk_config", "Ampico A Brilliant.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
