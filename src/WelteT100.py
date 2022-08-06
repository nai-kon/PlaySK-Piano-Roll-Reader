import numpy as np
from player import Player


class WelteT100(Player):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.bass_cres_pos = 0
        self.bass_cres_state = "slow_decres"
        self.bass_mf_hook = False
        self.bass_slow_cres_sec = 4.76   # min to max
        self.bass_slow_decres_sec = 4.76  # max to min
        self.bass_fast_cres_sec = 0.7
        self.bass_fast_decres_sec = 0.150

        self.treble_cres_pos = 0
        self.treble_cres_state = "slow_decres"
        self.treble_mf_hook = False
        self.treble_slow_cres_sec = 4.76   # min to max
        self.treble_slow_decres_sec = 4.76  # max to min
        self.treble_fast_cres_sec = 0.7
        self.treble_fast_decres_sec = 0.156

        self.mf_hook_pos = 0.5
        self.pre_time = None
        self.min_vacuum = 6     # in W.G
        self.max_vacuum = 35    # in W.G

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

        # bass
        cres_pos_min = 0
        cres_pos_max = 1
        if self.bass_mf_hook:
            if self.bass_cres_pos < self.mf_hook_pos:
                cres_pos_max = self.mf_hook_pos - 0.01
            else:
                cres_pos_min = self.mf_hook_pos + 0.01

        if self.bass_cres_state == "slow_cres":
            self.bass_cres_pos += (curtime - self.pre_time) * (1 / self.bass_slow_cres_sec)
        elif self.bass_cres_state == "slow_decres":
            self.bass_cres_pos -= (curtime - self.pre_time) * (1 / self.bass_slow_decres_sec)
        
        if self.holes["bass_forz_forte"]["is_open"]:
            self.bass_cres_pos += (curtime - self.pre_time) * (1 / self.bass_fast_cres_sec)
        elif self.holes["bass_forz_piano"]["is_open"]:
            self.bass_cres_pos -= (curtime - self.pre_time) * (1 / self.bass_fast_decres_sec)

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
            self.treble_cres_pos += (curtime - self.pre_time) * (1 / self.treble_slow_cres_sec)
        elif self.treble_cres_state == "slow_decres":
            self.treble_cres_pos -= (curtime - self.pre_time) * (1 / self.treble_slow_decres_sec)
        
        if self.holes["treble_forz_forte"]["is_open"]:
            self.treble_cres_pos += (curtime - self.pre_time) * (1 / self.treble_fast_cres_sec)
        elif self.holes["treble_forz_piano"]["is_open"]:
            self.treble_cres_pos -= (curtime - self.pre_time) * (1 / self.treble_fast_decres_sec)

        self.treble_cres_pos = max(self.treble_cres_pos, cres_pos_min)
        self.treble_cres_pos = min(self.treble_cres_pos, cres_pos_max)

        self.pre_time = curtime

    def calc_expression(self):
        def calc_vacuum(cres_pos):
            return self.min_vacuum + cres_pos * (self.max_vacuum - self.min_vacuum)

        self.bass_vacuum = calc_vacuum(self.bass_cres_pos)
        self.treble_vacuum = calc_vacuum(self.treble_cres_pos)

    def emulate_pedals(self):
        # sustain pedal
        if self.holes["sustain_on"]["is_open"]:
            self.midi.sustain_on()

        elif self.holes["sustain_off"]["is_open"]:
            self.midi.sustain_off()

        # hammer rail lift emulation
        if self.holes["soft_on"]["is_open"]:
            self.midi.hammer_lift_on()

        elif self.holes["soft_off"]["is_open"]:
            self.midi.hammer_lift_off()

    def draw_tracker(self, frame):
        # need override for drawing lock hole
        # self.holes["bass_mf_on"]["is_open"] = self.bass_mf_hook
        # self.holes["bass_intensity"]["is_open"][:] = self.bass_intensity_lock[:]
        # self.holes["treble_intensity"]["is_open"][:] = self.treble_intensity_lock[::-1]
        # self.holes["subintensity"]["is_open"][0] = self.bass_sub_intensity_lock or self.treble_sub_intensity_lock
        super().draw_tracker(frame)


if __name__ == "__main__":
    import time
    import os
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = WelteT100(os.path.join("config", "Ampico B white background.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
