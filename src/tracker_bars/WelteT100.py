import numpy as np
import wx

from .base_player import BasePlayer


class WelteT100(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.mf_hook_pos = 0.47
        self.loud_pos = 0.7
        self.min_vacuum = 5.7   # in W.G
        self.max_vacuum = 35    # in W.G
        self.cres_pos_to_vacuum = np.poly1d(np.polyfit((0, self.mf_hook_pos, 1), (self.min_vacuum, 20, self.max_vacuum), 2))

        self.bass_cres_pos = 0
        self.bass_cres_state = "slow_decres"
        self.bass_mf_hook = False
        self.bass_slow_cres_rate = self.mf_hook_pos / 2.38   # min to mf takes 2.38sec
        self.bass_slow_decres_rate = self.mf_hook_pos / 2.38   # mf to min takes 2.38sec
        self.bass_fast_cres_rate = 1 / 0.7
        self.bass_fast_decres_rate = 1 / 0.15

        self.treble_cres_pos = 0
        self.treble_cres_state = "slow_decres"
        self.treble_mf_hook = False
        self.treble_slow_cres_rate = self.mf_hook_pos / 2.38   # min to mf takes 2.38sec
        self.treble_slow_decres_rate = self.mf_hook_pos / 2.38   # mf to min takes 2.38sec
        self.treble_fast_cres_rate = 1 / 0.7
        self.treble_fast_decres_rate = 1 / 0.15

        self.pre_time = None
        self.bass_vacuum = self.min_vacuum
        self.treble_vacuum = self.min_vacuum

    def emulate_off(self):
        super().emulate_off()
        self.bass_cres_pos = 0
        self.bass_cres_state = "slow_decres"
        self.bass_mf_hook = False
        self.treble_cres_pos = 0
        self.treble_cres_state = "slow_decres"
        self.treble_mf_hook = False
        self.bass_vacuum = self.min_vacuum
        self.treble_vacuum = self.min_vacuum

    def emulate_expression(self, curtime):
        # Check bass expression holes
        if self.holes["bass_mf_on"]["to_open"]:
            self.bass_mf_hook = True
        elif self.holes["bass_mf_off"]["to_open"]:
            self.bass_mf_hook = False

        if self.holes["bass_cresc_forte"]["to_open"]:
            self.bass_cres_state = "slow_cres"
        elif self.holes["bass_cresc_piano"]["to_open"]:
            self.bass_cres_state = "slow_decres"

        # Check treble expression holes
        if self.holes["treble_mf_on"]["to_open"]:
            self.treble_mf_hook = True
        elif self.holes["treble_mf_off"]["to_open"]:
            self.treble_mf_hook = False

        if self.holes["treble_cresc_forte"]["to_open"]:
            self.treble_cres_state = "slow_cres"
        elif self.holes["treble_cresc_piano"]["to_open"]:
            self.treble_cres_state = "slow_decres"

        self.calc_crescendo(curtime)
        self.calc_expression()

    def calc_crescendo(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime
        delta_time = curtime - self.pre_time

        # # note on vacuum drop emulation
        # on_notes = self.holes["note"]["to_open"].nonzero()[0]
        # if on_notes.size > 0:
        #     for key in on_notes:
        #         if key < self.stack_split:
        #             self.bass_cres_pos -=0.004
        #         else:
        #             self.treble_cres_pos -= 0.004

        # bass
        cres_pos_min = 0
        cres_pos_max = 1
        if self.bass_mf_hook:
            if self.bass_cres_pos < self.mf_hook_pos:
                cres_pos_max = self.mf_hook_pos - 0.01
            else:
                cres_pos_min = self.mf_hook_pos + 0.01

        if self.bass_cres_state == "slow_cres":
            self.bass_cres_pos += delta_time * self.bass_slow_cres_rate
            if not (self.bass_mf_hook or self.holes["bass_forz_forte"]["is_open"]):
                self.bass_cres_pos = min(self.bass_cres_pos, self.loud_pos)
        elif self.bass_cres_state == "slow_decres":
            self.bass_cres_pos -= delta_time * self.bass_slow_decres_rate

        if self.holes["bass_forz_forte"]["is_open"]:
            self.bass_cres_pos += delta_time * self.bass_fast_cres_rate
        elif self.holes["bass_forz_piano"]["is_open"]:
            self.bass_cres_pos -= delta_time * self.bass_fast_decres_rate

        self.bass_cres_pos = max(self.bass_cres_pos, cres_pos_min)
        self.bass_cres_pos = min(self.bass_cres_pos, cres_pos_max)

        # treble
        cres_pos_min = 0
        cres_pos_max = 1
        if self.treble_mf_hook:
            if self.treble_cres_pos < self.mf_hook_pos:
                cres_pos_max = self.mf_hook_pos - 0.01
            else:
                cres_pos_min = self.mf_hook_pos + 0.01

        if self.treble_cres_state == "slow_cres":
            self.treble_cres_pos += delta_time * self.treble_slow_cres_rate
            if not (self.treble_mf_hook or self.holes["treble_forz_forte"]["is_open"]):
                self.treble_cres_pos = min(self.treble_cres_pos, self.loud_pos)
        elif self.treble_cres_state == "slow_decres":
            self.treble_cres_pos -= delta_time * self.treble_slow_decres_rate

        if self.holes["treble_forz_forte"]["is_open"]:
            self.treble_cres_pos += delta_time * self.treble_fast_cres_rate
        elif self.holes["treble_forz_piano"]["is_open"]:
            self.treble_cres_pos -= delta_time * self.treble_fast_decres_rate

        self.treble_cres_pos = max(self.treble_cres_pos, cres_pos_min)
        self.treble_cres_pos = min(self.treble_cres_pos, cres_pos_max)

        self.pre_time = curtime

    def calc_expression(self):
        self.bass_vacuum, self.treble_vacuum = self.cres_pos_to_vacuum((self.bass_cres_pos, self.treble_cres_pos))

    def emulate_pedals(self):
        # sustain pedal
        if self.holes["sustain_on"]["is_open"]:
            self.midi.sustain_on()

        elif self.holes["sustain_off"]["is_open"]:
            self.midi.sustain_off()

        # soft pedal
        if self.holes["soft_on"]["is_open"]:
            self.midi.soft_on()

        elif self.holes["soft_off"]["is_open"]:
            self.midi.soft_off()

    def draw_tracker(self, wxdc: wx.PaintDC):
        # need override for drawing lock hole
        # self.holes["bass_mf_on"]["is_open"] = self.bass_mf_hook
        # self.holes["bass_intensity"]["is_open"][:] = self.bass_intensity_lock[:]
        # self.holes["treble_intensity"]["is_open"][:] = self.treble_intensity_lock[::-1]
        # self.holes["subintensity"]["is_open"][0] = self.bass_sub_intensity_lock or self.treble_sub_intensity_lock
        super().draw_tracker(wxdc)


if __name__ == "__main__":
    import os
    import time

    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = WelteT100(os.path.join("playsk_config", "Welte T100.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
