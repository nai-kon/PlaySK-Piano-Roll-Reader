from .WelteT100 import WelteT100


class WelteLicensee(WelteT100):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.bass_slow_cres_rate = self.mf_hook_pos / 2.45   # min to mf takes 2.45sec
        self.bass_slow_decres_rate = self.mf_hook_pos / 2.45   # mf to min takes 2.45sec
        self.bass_fast_cres_rate = 1 / 0.58
        self.bass_fast_decres_rate = 1 / 0.15

        self.treble_slow_cres_rate = self.mf_hook_pos / 2.45   # min to mf takes 2.5sec
        self.treble_slow_decres_rate = self.mf_hook_pos / 2.45   # mf to min takes 2.5sec
        self.treble_fast_cres_rate = 1 / 0.58
        self.treble_fast_decres_rate = 1 / 0.15

        self.bass_vacuum = self.min_vacuum
        self.treble_vacuum = self.min_vacuum

    def emulate_pedals(self):
        # sustain pedal
        if self.holes["sustain_on"]["is_open"]:
            self.midi.sustain_on()

        elif self.holes["sustain_off"]["is_open"]:
            self.midi.sustain_off()

        # licensee uses hammer lift
        if self.holes["soft_on"]["is_open"]:
            self.midi.hammer_lift_on()

        elif self.holes["soft_off"]["is_open"]:
            self.midi.hammer_lift_off()


if __name__ == "__main__":
    import os
    import time

    import numpy as np
    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = WelteLicensee(os.path.join("playsk_config", "Welte Licensee white back.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
