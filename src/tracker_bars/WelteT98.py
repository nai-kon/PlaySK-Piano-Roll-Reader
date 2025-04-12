from .WelteT100 import WelteT100


class WelteT98(WelteT100):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.bass_slow_cres_rate = self.mf_hook_pos / 2.45   # min to mf takes 2.5sec
        self.bass_slow_decres_rate = self.mf_hook_pos / 2.45   # mf to min takes 2.5sec
        self.bass_fast_cres_rate = 1 / 0.85
        self.bass_fast_decres_rate = 1 / 0.18

        self.treble_slow_cres_rate = self.mf_hook_pos / 2.45   # min to mf takes 2.5sec
        self.treble_slow_decres_rate = self.mf_hook_pos / 2.45   # mf to min takes 2.5sec
        self.treble_fast_cres_rate = 1 / 0.85
        self.treble_fast_decres_rate = 1 / 0.18

        self.bass_vacuum = self.min_vacuum
        self.treble_vacuum = self.min_vacuum

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
            self.midi.soft_on()

        elif soft["to_close"]:
            self.midi.soft_off()

    def emulate_expression(self, curtime):
        # Check bass expression holes
        if self.holes["bass_mf"]["is_open"]:
            self.bass_mf_hook = True
        else:
            self.bass_mf_hook = False

        if self.holes["bass_cresc"]["is_open"]:
            self.bass_cres_state = "slow_cres"
        else:
            self.bass_cres_state = "slow_decres"

        # Check treble expression holes
        if self.holes["treble_mf"]["is_open"]:
            self.treble_mf_hook = True
        else:
            self.treble_mf_hook = False

        if self.holes["treble_cresc"]["is_open"]:
            self.treble_cres_state = "slow_cres"
        else:
            self.treble_cres_state = "slow_decres"

        self.calc_crescendo(curtime)
        self.calc_expression()


if __name__ == "__main__":
    import os
    import time

    import numpy as np

    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = WelteT98(os.path.join("playsk_config", "Ampico B white back.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
